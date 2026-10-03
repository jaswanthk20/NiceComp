import math
import re
from sqlalchemy import select, text
from .models import Chunk, Document, DocumentModel
from .providers import embeddings, chat_model
from .domain import safety_check
from .observability import event

UNKNOWN = "I couldn't verify that from the available Nice Compressors documentation. Please create a support ticket or contact support."
STOPWORDS = set(
    "what which should i my the a an is are for to do does this it use how often please show technical specifications compressor".split()
)
TOPICS = {
    "oil": r"oil|lubric",
    "electrical": r"electrical|voltage|volt|wiring|phase|amp",
    "service": r"service|interval|maintenance",
    "pressure": r"pressure|psi|bar",
    "torque": r"torque",
    "tank": r"tank|receiver|litre|liter",
}


def relevant(question, excerpt):
    q = question.lower()
    e = excerpt.lower()
    topics = [pattern for pattern in TOPICS.values() if re.search(pattern, q)]
    if topics and not all(re.search(pattern, e) for pattern in topics):
        return False
    if ("oil" in q or "lubric" in q) and not re.search(r"iso|sae|grade|type|oil:", e):
        return False
    if re.search(TOPICS["electrical"], q) and not re.search(
        r"\b\d+\s*(v\b|volts?|hz|amps?|phase)", e
    ):
        return False
    if re.search(r"interval|how often|service", q) and not re.search(
        r"\d+\s*(hours?|months?|days?)", e
    ):
        return False
    if re.search(r"pressure|psi|bar", q) and not re.search(r"\d+.*(bar|psi|pressure)", e):
        return False
    words = set(re.findall(r"\w+", q)) - STOPWORDS
    return bool(words & set(re.findall(r"\w+", e))) or "specification" in q


def retrieve(db, model_id, question):
    provider = embeddings()
    vector = provider.embed(question)
    if db.bind.dialect.name == "postgresql":
        ids = (
            db.execute(
                text("""SELECT c.id FROM document_chunks c
            JOIN documents d ON d.id=c.document_id JOIN document_models dm ON dm.document_id=d.id
            WHERE dm.model_id=:model AND d.active AND d.approved AND d.status='indexed'
            AND c.embedding_model=:provider AND c.embedding_vector IS NOT NULL
            ORDER BY c.embedding_vector <=> CAST(:vector AS extensions.vector) LIMIT 8"""),
                {"model": model_id, "provider": provider.name, "vector": str(vector)},
            )
            .scalars()
            .all()
        )
        ids = [str(i) for i in ids]
        rows = db.execute(select(Chunk, Document).join(Document).where(Chunk.id.in_(ids))).all()
        rows.sort(key=lambda pair: ids.index(pair[0].id))
    else:
        rows = db.execute(
            select(Chunk, Document)
            .join(Document)
            .join(DocumentModel, DocumentModel.document_id == Document.id)
            .where(
                DocumentModel.model_id == model_id,
                Document.active.is_(True),
                Document.approved.is_(True),
                Document.status == "indexed",
                Chunk.embedding_model == provider.name,
            )
        ).all()

        def cosine(pair):
            v = pair[0].embedding
            return sum(a * b for a, b in zip(v, vector)) / (
                math.sqrt(sum(x * x for x in v)) * math.sqrt(sum(x * x for x in vector)) or 1
            )

        rows = sorted(rows, key=cosine, reverse=True)[:8]
    matches = [(c, d) for c, d in rows if relevant(question, c.text)]
    event("rag.retrieval", model_id=model_id, matches=len(matches))
    return matches


def answer(db, model_id, question):
    safety = safety_check(question)
    if safety:
        return {"answer": safety, "sources": [], "escalate": True, "mode": "safety"}
    rows = retrieve(db, model_id, question)
    if not rows:
        return {"answer": UNKNOWN, "sources": [], "escalate": True, "mode": "unverified"}
    quotes = chat_model().select_quotes(question, [c.text for c, d in rows])
    accepted = []
    sources = []
    if not isinstance(quotes, list):
        quotes = []
    for quote in quotes[:3]:
        if not isinstance(quote, str) or len(quote) < 8 or len(quote) > 900 or safety_check(quote):
            continue
        for chunk, document in rows:
            # Grounding is enforced in code; model-generated unsupported words never reach the user.
            if quote == chunk.text and relevant(question, quote):
                if quote not in accepted:
                    accepted.append(quote)
                    sources.append(
                        {
                            "document_id": document.id,
                            "chunk_id": chunk.id,
                            "title": document.title,
                            "url": document.source_url,
                            "page": chunk.page,
                            "section": chunk.section,
                            "version": document.version,
                        }
                    )
                break
    return {
        "answer": "From the documentation for your selected model:\n\n" + "\n\n".join(accepted)
        if accepted
        else UNKNOWN,
        "sources": sources,
        "escalate": not bool(accepted),
        "mode": "grounded_quotes" if accepted else "unverified",
    }
