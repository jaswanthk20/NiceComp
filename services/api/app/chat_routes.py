from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from .auth import current_user, require_customer, limiter
from .db import get_db
from .models import ChatSession, ChatMessage, Document, DocumentModel
from .portal import owned
from .schemas import ChatInput
from .rag import answer

router = APIRouter()


@router.get("/products/{asset_id}/documents")
def documents(asset_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    asset = owned(db, user, asset_id)
    return db.scalars(
        select(Document)
        .join(DocumentModel)
        .where(
            DocumentModel.model_id == asset.model_id,
            Document.active.is_(True),
            Document.approved.is_(True),
        )
    ).all()


@router.get("/chat/{asset_id}")
def history(asset_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    owned(db, user, asset_id)
    sessions = db.scalars(
        select(ChatSession)
        .where(
            ChatSession.customer_id == user.customer_id,
            ChatSession.customer_product_id == str(asset_id),
        )
        .order_by(ChatSession.created_at)
    ).all()
    if not sessions:
        return {"session_id": None, "messages": []}
    session = sessions[-1]
    return {
        "session_id": session.id,
        "messages": db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
        ).all(),
    }


@router.post("/chat")
def chat(body: ChatInput, user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    limiter.check(("chat", user.id), maximum=12)
    asset = owned(db, user, body.customer_product_id)
    if asset.customer_id != user.customer_id:
        raise HTTPException(404, "Product not found.")
    session = None
    if body.session_id:
        session = db.scalar(
            select(ChatSession).where(
                ChatSession.id == str(body.session_id),
                ChatSession.customer_id == user.customer_id,
                ChatSession.customer_product_id == asset.id,
            )
        )
        if not session:
            raise HTTPException(404, "Conversation not found.")
    try:
        result = answer(db, asset.model_id, body.question)
    except Exception:
        raise HTTPException(503, "NICE AI is unavailable. Retry or create a support ticket.")
    if not session:
        session = ChatSession(customer_id=user.customer_id, customer_product_id=asset.id)
        db.add(session)
        db.flush()
    db.add(ChatMessage(session_id=session.id, role="user", content=body.question))
    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["answer"],
            sources=result["sources"],
        )
    )
    db.flush()
    return {**result, "session_id": session.id}
