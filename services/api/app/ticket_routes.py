from uuid import UUID
import uuid
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from .auth import current_user, require_customer, owner_filter, limiter
from .db import get_db
from .models import (
    Ticket,
    TicketImage,
    TicketEvent,
    IssueCategory,
    SLARule,
    EmailEvent,
    utcnow,
    uid,
)
from .schemas import TicketInput
from .portal import owned, product_view, private_link
from .domain import severity_for, business_due
from .storage import storage, clean_photo, MAX_UPLOAD

router = APIRouter()


def utc_timestamp(value):
    return value.replace(tzinfo=value.tzinfo or timezone.utc) if value else None


def get_ticket(db, user, ticket_id):
    ticket = db.scalar(
        owner_filter(select(Ticket).where(Ticket.id == str(ticket_id)), Ticket.customer_id, user)
    )
    if not ticket:
        raise HTTPException(404, "Ticket not found.")
    return ticket


def ticket_view(ticket):
    return {
        key: getattr(ticket, key)
        for key in (
            "id",
            "number",
            "customer_product_id",
            "category",
            "severity",
            "description",
            "approved_summary",
            "status",
            "created_at",
        )
    } | {
        "created_at": utc_timestamp(ticket.created_at),
        "response_due_at": utc_timestamp(ticket.response_due_at) if ticket.sla_official else None,
        "resolution_due_at": utc_timestamp(ticket.resolution_due_at)
        if ticket.sla_official
        else None,
        "sla_message": None
        if ticket.sla_official
        else "Response target pending company configuration.",
    }


@router.get("/categories")
def categories(user=Depends(current_user), db=Depends(get_db)):
    return db.scalars(
        select(IssueCategory.name)
        .where(IssueCategory.enabled.is_(True))
        .order_by(IssueCategory.name)
    ).all()


@router.post("/images", status_code=201)
async def upload_image(
    file: UploadFile = File(...), user=Depends(current_user), db=Depends(get_db)
):
    require_customer(user)
    limiter.check(("upload", user.id), maximum=12)
    data = await file.read(MAX_UPLOAD + 1)
    content = clean_photo(data)
    image = TicketImage(
        id=uid(), customer_id=user.customer_id, name="Diagnostic photo.jpg", storage_path=""
    )
    image.storage_path = f"{user.customer_id}/photos/{image.id}.jpg"
    try:
        storage().put(image.storage_path, content, "image/jpeg")
    except Exception:
        raise HTTPException(503, "Photo upload failed. Please retry.")
    db.add(image)
    db.flush()
    return {"id": image.id, "name": image.name}


@router.get("/images/{image_id}/url")
def image_url(image_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    image = db.scalar(
        owner_filter(
            select(TicketImage).where(TicketImage.id == str(image_id)),
            TicketImage.customer_id,
            user,
        )
    )
    if not image:
        raise HTTPException(404, "Photo not found.")
    return private_link(image.storage_path, "image/jpeg")


@router.post("/tickets", status_code=201)
def create_ticket(body: TicketInput, user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    existing = db.scalar(
        select(Ticket).where(
            Ticket.customer_id == user.customer_id,
            Ticket.idempotency_key == str(body.idempotency_key),
        )
    )
    if existing:
        return ticket_view(existing)
    limiter.check(("ticket", user.id), maximum=10)
    asset = owned(db, user, body.customer_product_id)
    if asset.customer_id != user.customer_id:
        raise HTTPException(404, "Product not found.")
    category = db.get(IssueCategory, body.category)
    if not category or not category.enabled:
        raise HTTPException(422, "Choose an available issue category.")
    images = db.scalars(
        select(TicketImage)
        .where(
            TicketImage.id.in_([str(i) for i in body.image_ids]),
            TicketImage.customer_id == user.customer_id,
            TicketImage.ticket_id.is_(None),
        )
        .with_for_update()
    ).all()
    if len(images) != len(body.image_ids):
        raise HTTPException(422, "One or more photos are unavailable. Attach them again.")
    now = utcnow()
    severity = severity_for(body.description, body.severity)
    ticket = Ticket(
        id=uid(),
        number=f"NC-{now.year}-{uuid.uuid4().hex[:12].upper()}",
        customer_id=user.customer_id,
        customer_product_id=asset.id,
        category=body.category,
        severity=severity,
        description=body.description,
        approved_summary=body.approved_summary,
        idempotency_key=str(body.idempotency_key),
        created_at=now,
    )
    rule = db.scalar(select(SLARule).where(SLARule.severity == severity))
    if rule:
        ticket.response_due_at = business_due(now, rule.response_minutes, rule)
        ticket.resolution_due_at = business_due(now, rule.resolution_minutes, rule)
        ticket.sla_official = rule.official
        ticket.escalation_minutes = rule.escalation_minutes
    db.add(ticket)
    db.flush()
    for image in images:
        image.ticket_id = ticket.id
    db.add(
        TicketEvent(ticket_id=ticket.id, status="Open", note="Ticket submitted.", actor_id=user.id)
    )
    db.add(EmailEvent(ticket_id=ticket.id))
    db.flush()
    return ticket_view(ticket)


@router.get("/tickets")
def tickets(user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    return [
        ticket_view(t)
        for t in db.scalars(
            select(Ticket)
            .where(Ticket.customer_id == user.customer_id)
            .order_by(Ticket.created_at.desc())
        ).all()
    ]


@router.get("/tickets/{ticket_id}")
def ticket(ticket_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    item = get_ticket(db, user, ticket_id)
    return {
        "ticket": ticket_view(item),
        "product": product_view(db, owned(db, user, item.customer_product_id)),
        "images": [
            {"id": i.id, "name": i.name}
            for i in db.scalars(select(TicketImage).where(TicketImage.ticket_id == item.id)).all()
        ],
        "events": [
            {
                "id": event.id,
                "status": event.status,
                "note": event.note,
                "created_at": utc_timestamp(event.created_at),
            }
            for event in db.scalars(
                select(TicketEvent)
                .where(TicketEvent.ticket_id == item.id)
                .order_by(TicketEvent.created_at)
            ).all()
        ],
        "email_status": db.scalar(select(EmailEvent.state).where(EmailEvent.ticket_id == item.id)),
    }
