import hashlib
import io
import re
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sqlalchemy import delete, text
from .models import Document, DocumentModel, Chunk
from .providers import embeddings
from .observability import event

OFFICIAL_HOSTS = {
    "www.nicecompressors.net",
    "nicecompressors.net",
    "nice-compressors-company6.odoo.com",
}


def official_url(url):
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in OFFICIAL_HOSTS
        and parsed.port in (None, 443)
        and not parsed.username
        and not parsed.password
    )


def download_document(url):
    if not official_url(url):
        raise ValueError("Only approved official HTTPS sources are permitted")
    # No automatic redirects: every redirect target is checked before any network request.
    for _ in range(4):
        with httpx.stream("GET", url, follow_redirects=False, timeout=30) as r:
            if r.is_redirect:
                from urllib.parse import urljoin

                url = urljoin(url, r.headers["location"])
                if not official_url(url):
                    raise ValueError("Redirect leaves official sources")
                continue
            r.raise_for_status()
            raw = bytearray()
            for part in r.iter_bytes():
                raw.extend(part)
                if len(raw) > 20_000_000:
                    raise ValueError("Document exceeds 20 MB")
            if url.lower().endswith(".pdf") and not raw.startswith(b"%PDF-"):
                raise ValueError("PDF URL returned non-PDF content")
            return bytes(raw)
    raise ValueError("Too many redirects")


def extract(raw: bytes):
    if raw.startswith(b"%PDF-"):
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported")
        if len(reader.pages) > 500:
            raise ValueError("PDF exceeds 500 pages")
        pages = [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
        if not any(t.strip() for _, t in pages):
            raise ValueError("Scanned PDF needs reviewed OCR before ingestion")
        return pages
    soup = BeautifulSoup(raw, "html.parser")
    for item in soup(["script", "style", "nav", "header", "footer"]):
        item.decompose()
    main = soup.find("main") or soup
    if main.find("table"):
        raise ValueError(
            "Tabular product pages require reviewed per-model excerpts to avoid mixed specifications"
        )
    return [(None, main.get_text(" ", strip=True))]


def split_chunks(text_value, maximum=900):
    clean = re.sub(r"\s+", " ", text_value).strip()
    pieces = []
    while clean:
        if len(clean) <= maximum:
            pieces.append(clean)
            break
        cut = clean.rfind(" ", 0, maximum)
        if cut < 1:
            cut = maximum
        pieces.append(clean[:cut])
        clean = clean[cut:].lstrip()
    return pieces


def index_document(db, document, pages):
    provider = embeddings()
    # Build first: a failed embedding call leaves the previously indexed version intact.
    prepared = [
        (page, part, provider.embed(part))
        for page, content in pages
        for part in split_chunks(content)
    ]
    if not prepared:
        raise ValueError("No text to index")
    db.execute(delete(Chunk).where(Chunk.document_id == document.id))
    for page, part, vector in prepared:
        chunk = Chunk(
            document_id=document.id,
            text=part,
            page=page,
            section=document.title,
            embedding=vector,
            embedding_model=provider.name,
        )
        db.add(chunk)
        db.flush()
        if db.bind.dialect.name == "postgresql":
            db.execute(
                text(
                    "UPDATE document_chunks SET embedding_vector=CAST(:v AS extensions.vector) WHERE id=:id"
                ),
                {"v": str(vector), "id": chunk.id},
            )
    document.status = "indexed"
    document.error = None
    event("document.indexed", document_id=document.id, chunks=len(prepared))
    db.flush()


def create_document(db, title, url, version, family, model_ids, raw, kind="manual"):
    if not official_url(url):
        raise ValueError("Supply an official source URL")
    doc = Document(
        title=title,
        source_url=url,
        version=version,
        family=family,
        sha256=hashlib.sha256(raw).hexdigest(),
        kind=kind,
    )
    db.add(doc)
    db.flush()
    for model_id in set(model_ids):
        db.add(DocumentModel(document_id=doc.id, model_id=model_id))
    db.flush()
    return doc
