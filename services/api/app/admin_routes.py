from uuid import UUID
from datetime import timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import Field
from sqlalchemy import select
from .auth import admin, staff
from .db import get_db
from .models import (
    Ticket,
    TicketEvent,
    Customer,
    Profile,
    Product,
    ProductModel,
    OwnedProduct,
    Warranty,
    SLARule,
    IssueCategory,
    Document,
    EmailEvent,
    SyncEvent,
    AuditEvent,
    utcnow,
)
from .schemas import StatusInput, SLAInput, MappingInput, WarrantyInput, CategoryInput, Input
from .domain import TRANSITIONS
from .knowledge import create_document, index_document, extract, download_document
from .storage import storage
from .pos import CSVImportConnector, OdooConnector, synchronize

router = APIRouter(prefix="/admin")


def audit(db, user, action, resource):
    db.add(AuditEvent(actor_id=user.id, action=action, resource_id=str(resource)))


@router.get("/tickets")
def tickets(priority: str | None = None, user=Depends(staff), db=Depends(get_db)):
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if priority:
        query = query.where(Ticket.severity == priority)
    now = utcnow()

    def breach(t):
        due = t.response_due_at
        return bool(
            due and not t.responded_at and due.replace(tzinfo=due.tzinfo or timezone.utc) < now
        )

    return [
        {"ticket": t, "customer": db.get(Customer, t.customer_id), "response_breached": breach(t)}
        for t in db.scalars(query).all()
    ]


@router.patch("/tickets/{ticket_id}")
def update_ticket(ticket_id: UUID, body: StatusInput, user=Depends(staff), db=Depends(get_db)):
    ticket = db.scalar(select(Ticket).where(Ticket.id == str(ticket_id)).with_for_update())
    if not ticket:
        raise HTTPException(404, "Ticket not found.")
    if body.status not in TRANSITIONS[ticket.status]:
        raise HTTPException(409, "That status transition is not available.")
    ticket.status = body.status
    if not ticket.responded_at:
        ticket.responded_at = utcnow()
    if body.status == "Resolved":
        ticket.resolved_at = utcnow()
    if body.status == "In Progress":
        ticket.resolved_at = None
    db.add(TicketEvent(ticket_id=ticket.id, status=body.status, note=body.note, actor_id=user.id))
    audit(db, user, "ticket.status", ticket.id)
    return {"status": ticket.status}


@router.get("/sla")
def sla(user=Depends(staff), db=Depends(get_db)):
    return db.scalars(select(SLARule)).all()


@router.put("/sla")
def configure_sla(body: SLAInput, user=Depends(admin), db=Depends(get_db)):
    rule = db.scalar(select(SLARule).where(SLARule.severity == body.severity))
    if not rule:
        rule = SLARule()
        db.add(rule)
    for key, value in body.model_dump().items():
        setattr(rule, key, value)
    audit(db, user, "sla.configure", body.severity)
    db.flush()
    return rule


@router.get("/customers")
def customers(user=Depends(admin), db=Depends(get_db)):
    return {
        "customers": db.scalars(select(Customer)).all(),
        "profiles": db.scalars(select(Profile)).all(),
    }


@router.put("/customer-mapping")
def associate(body: MappingInput, user=Depends(admin), db=Depends(get_db)):
    profile = db.get(Profile, str(body.user_id))
    customer = db.get(Customer, str(body.customer_id))
    if not profile or not customer:
        raise HTTPException(404, "Account or customer not found.")
    profile.customer_id = customer.id
    audit(db, user, "customer.associate", profile.id)
    return {"associated": True}


@router.put("/warranties/{asset_id}")
def adjust_warranty(asset_id: UUID, body: WarrantyInput, user=Depends(admin), db=Depends(get_db)):
    if not db.get(OwnedProduct, str(asset_id)):
        raise HTTPException(404, "Product not found.")
    warranty = db.scalar(select(Warranty).where(Warranty.customer_product_id == str(asset_id)))
    if not warranty:
        warranty = Warranty(customer_product_id=str(asset_id))
        db.add(warranty)
    for key, value in body.model_dump().items():
        setattr(warranty, key, value)
    warranty.adjusted_by = user.id
    audit(db, user, "warranty.adjust", asset_id)
    return {"updated": True}


@router.put("/categories")
def category(body: CategoryInput, user=Depends(admin), db=Depends(get_db)):
    item = db.get(IssueCategory, body.name)
    if not item:
        item = IssueCategory(name=body.name)
        db.add(item)
    item.enabled = body.enabled
    audit(db, user, "category.configure", body.name)
    return {"updated": True}


@router.get("/models")
def models(user=Depends(staff), db=Depends(get_db)):
    return [
        {
            "id": m.id,
            "name": m.name,
            "family": p.family,
            "source": m.source,
            "source_id": m.source_id,
        }
        for m, p in db.execute(select(ProductModel, Product).join(Product)).all()
    ]


class ModelInput(Input):
    family: str = Field(min_length=2, max_length=160)
    name: str = Field(min_length=2, max_length=120)
    source: str = Field(pattern="^(csv|odoo)$")
    source_id: str = Field(min_length=1, max_length=120)
    official_url: str
    image_url: str | None = None


@router.post("/models")
def model_create(body: ModelInput, user=Depends(admin), db=Depends(get_db)):
    from .knowledge import official_url

    if not official_url(body.official_url):
        raise HTTPException(422, "Use an official product URL.")
    if body.image_url and not official_url(body.image_url):
        raise HTTPException(422, "Use an official product image URL.")
    product = Product(
        family=body.family, name=body.name, official_url=body.official_url, image_url=body.image_url
    )
    db.add(product)
    db.flush()
    model = ProductModel(
        product_id=product.id, name=body.name, source=body.source, source_id=body.source_id
    )
    db.add(model)
    db.flush()
    audit(db, user, "model.create", model.id)
    return model


@router.get("/documents")
def documents(user=Depends(staff), db=Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.title, Document.version)).all()


@router.post("/documents", status_code=201)
async def upload_document(
    title: str = Form(max_length=200),
    source_url: str = Form(),
    version: str = Form(max_length=80),
    family: str = Form(max_length=160),
    model_ids: str = Form(),
    file: UploadFile = File(),
    user=Depends(admin),
    db=Depends(get_db),
):
    raw = await file.read(20_000_001)
    if len(raw) > 20_000_000 or not raw.startswith(b"%PDF-"):
        raise HTTPException(422, "Upload a valid PDF under 20 MB.")
    try:
        ids = [str(UUID(i.strip())) for i in model_ids.split(",")]
        if not ids or any(not db.get(ProductModel, i) for i in ids):
            raise ValueError()
        doc = create_document(db, title, source_url, version, family, ids, raw)
        path = f"knowledge/{doc.id}.pdf"
        storage().put(path, raw, "application/pdf")
        doc.storage_path = path
    except ValueError:
        raise HTTPException(422, "Check official source URL and applicable models.")
    audit(db, user, "document.upload", doc.id)
    return doc


@router.post("/documents/{document_id}/index")
def reindex(document_id: UUID, user=Depends(admin), db=Depends(get_db)):
    doc = db.get(Document, str(document_id))
    if not doc:
        raise HTTPException(404, "Document not found.")
    try:
        raw = (
            storage().get(doc.storage_path)
            if doc.storage_path
            else download_document(doc.source_url)
        )
        index_document(db, doc, extract(raw))
    except Exception:
        doc.status = "failed"
        doc.error = "Indexing failed. Check source format and embedding provider."
        return {"status": "failed", "message": doc.error}
    audit(db, user, "document.index", doc.id)
    return {"status": "indexed"}


class ApprovalInput(Input):
    active: bool
    reviewed_model_scope: bool


@router.patch("/documents/{document_id}")
def approve(document_id: UUID, body: ApprovalInput, user=Depends(admin), db=Depends(get_db)):
    doc = db.get(Document, str(document_id))
    if not doc:
        raise HTTPException(404, "Document not found.")
    if body.active and (doc.status != "indexed" or not body.reviewed_model_scope):
        raise HTTPException(422, "Index and review model applicability first.")
    doc.approved = body.reviewed_model_scope
    doc.active = body.active
    # Activation never silently overrides another version; require explicit deactivation first.
    if body.active and db.scalar(
        select(Document.id).where(
            Document.source_url == doc.source_url, Document.id != doc.id, Document.active.is_(True)
        )
    ):
        raise HTTPException(409, "Deactivate the previous version before activating this one.")
    audit(db, user, "document.approval", doc.id)
    return {"active": doc.active}


@router.post("/sync/import")
async def import_export(file: UploadFile = File(), user=Depends(admin), db=Depends(get_db)):
    raw = await file.read(5_000_001)
    try:
        connector = CSVImportConnector(raw)
        with db.begin_nested():
            count = synchronize(db, connector, "csv")
    except Exception:
        db.add(
            SyncEvent(
                source="csv", status="failed", error="Invalid export, mapping or source conflict"
            )
        )
        return {
            "status": "failed",
            "message": "Import failed. Verify the export schema and model mappings.",
        }
    audit(db, user, "sync.import", "csv")
    return {"status": "synced", "rows": count}


@router.post("/sync/odoo")
def odoo_sync(user=Depends(admin), db=Depends(get_db)):
    try:
        with db.begin_nested():
            count = synchronize(db, OdooConnector(), "odoo")
    except Exception:
        db.add(
            SyncEvent(
                source="odoo", status="failed", error="Odoo unavailable or configuration unverified"
            )
        )
        return {
            "status": "failed",
            "message": "Odoo access or field mapping is not verified. See docs/ODOO.md.",
        }
    audit(db, user, "sync.odoo", "odoo")
    return {"status": "synced", "rows": count}


@router.get("/events")
def events(user=Depends(staff), db=Depends(get_db)):
    return {
        "email": db.scalars(
            select(EmailEvent).order_by(EmailEvent.next_attempt_at.desc()).limit(100)
        ).all(),
        "sync": db.scalars(
            select(SyncEvent).order_by(SyncEvent.last_synced_at.desc()).limit(100)
        ).all(),
    }


@router.post("/email/{event_id}/retry")
def retry_email(event_id: UUID, user=Depends(admin), db=Depends(get_db)):
    event = db.get(EmailEvent, str(event_id))
    if not event:
        raise HTTPException(404, "Email event not found.")
    if event.state == "sent":
        raise HTTPException(409, "Email was already sent.")
    event.state = "pending"
    event.attempts = 0
    event.next_attempt_at = utcnow()
    audit(db, user, "email.retry", event.id)
    return {"queued": True}


@router.post("/receipts/{purchase_id}", status_code=201)
async def import_receipt(
    purchase_id: UUID, file: UploadFile = File(), user=Depends(admin), db=Depends(get_db)
):
    from .models import Purchase, Receipt, uid
    from .pdf_render import validate_receipt

    purchase = db.get(Purchase, str(purchase_id))
    if not purchase:
        raise HTTPException(404, "Purchase not found.")
    raw = await file.read(20_000_001)
    if len(raw) > 20_000_000 or not raw.startswith(b"%PDF-"):
        raise HTTPException(422, "Choose a PDF under 20 MB.")
    try:
        validate_receipt(raw)
    except Exception:
        raise HTTPException(422, "Receipt PDF cannot be read or exceeds 30 pages.")
    receipt = Receipt(
        id=uid(), purchase_id=purchase.id, name="Purchase receipt.pdf", storage_path=""
    )
    receipt.storage_path = f"{purchase.customer_id}/receipts/{receipt.id}.pdf"
    storage().put(receipt.storage_path, raw, "application/pdf")
    db.add(receipt)
    audit(db, user, "receipt.import", receipt.id)
    return {"id": receipt.id}
