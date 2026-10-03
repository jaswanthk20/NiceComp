"""Relational domain model. JSON is reserved for citations, calendar days and vectors in portable review."""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Date,
    DateTime,
    Integer,
    Boolean,
    Numeric,
    JSON,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column as col


def utcnow():
    return datetime.now(timezone.utc)


def uid():
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Entity:
    id = col(Uuid(as_uuid=False), primary_key=True, default=uid)


class Customer(Entity, Base):
    __tablename__ = "customers"
    name = col(String(160), nullable=False)
    email = col(String(254), nullable=False)
    phone = col(String(40))
    source = col(String(30), nullable=False)
    source_id = col(String(120), nullable=False)
    __table_args__ = (UniqueConstraint("source", "source_id"),)


class Profile(Base):
    __tablename__ = "customer_profiles"
    id = col(Uuid(as_uuid=False), primary_key=True)
    customer_id = col(ForeignKey("customers.id"), index=True)
    display_name = col(String(160), nullable=False)
    role = col(String(20), default="customer", nullable=False)


class DevCredential(Base):
    __tablename__ = "development_credentials"
    user_id = col(ForeignKey("customer_profiles.id"), primary_key=True)
    email = col(String(254), unique=True, nullable=False)
    password_hash = col(String(256), nullable=False)


class Product(Entity, Base):
    __tablename__ = "products"
    family = col(String(160), nullable=False)
    name = col(String(200), nullable=False)
    official_url = col(Text)
    image_url = col(Text)


class ProductModel(Entity, Base):
    __tablename__ = "product_models"
    product_id = col(ForeignKey("products.id"), nullable=False, index=True)
    name = col(String(120), nullable=False)
    source = col(String(30), nullable=False)
    source_id = col(String(120), nullable=False)
    __table_args__ = (UniqueConstraint("source", "source_id"),)


class Purchase(Entity, Base):
    __tablename__ = "purchases"
    customer_id = col(ForeignKey("customers.id"), nullable=False, index=True)
    source = col(String(30), nullable=False)
    source_id = col(String(120), nullable=False)
    invoice_number = col(String(120), nullable=False)
    purchased_on = col(Date, nullable=False)
    currency = col(String(3), nullable=False)
    amount = col(Numeric(14, 2))
    payment_status = col(String(80))
    last_synced_at = col(DateTime(timezone=True), default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("source", "source_id"),)


class PurchaseItem(Entity, Base):
    __tablename__ = "purchase_items"
    purchase_id = col(ForeignKey("purchases.id"), nullable=False, index=True)
    model_id = col(ForeignKey("product_models.id"), nullable=False)
    source_line_id = col(String(120), nullable=False)
    quantity = col(Integer, nullable=False)
    amount = col(Numeric(14, 2))
    __table_args__ = (UniqueConstraint("purchase_id", "source_line_id"),)


class OwnedProduct(Entity, Base):
    __tablename__ = "customer_products"
    customer_id = col(ForeignKey("customers.id"), nullable=False, index=True)
    model_id = col(ForeignKey("product_models.id"), nullable=False)
    purchase_item_id = col(ForeignKey("purchase_items.id"), nullable=False, index=True)
    serial = col(String(120))
    source_asset_id = col(String(120), nullable=False)
    __table_args__ = (UniqueConstraint("purchase_item_id", "source_asset_id"),)


class Warranty(Entity, Base):
    __tablename__ = "warranties"
    customer_product_id = col(ForeignKey("customer_products.id"), unique=True, nullable=False)
    starts_on = col(Date)
    ends_on = col(Date)
    basis = col(String(40), nullable=False)
    evidence = col(Text, nullable=False)
    adjusted_by = col(Uuid(as_uuid=False))


class Receipt(Entity, Base):
    __tablename__ = "receipts"
    purchase_id = col(ForeignKey("purchases.id"), nullable=False, index=True)
    storage_path = col(Text, nullable=False)
    name = col(String(180), nullable=False)


class Document(Entity, Base):
    __tablename__ = "documents"
    title = col(String(200), nullable=False)
    source_url = col(Text, nullable=False)
    version = col(String(80), nullable=False)
    published_on = col(Date)
    family = col(String(160), nullable=False)
    sha256 = col(String(64), nullable=False)
    storage_path = col(Text)
    active = col(Boolean, default=False, nullable=False)
    approved = col(Boolean, default=False, nullable=False)
    status = col(String(30), default="pending", nullable=False)
    error = col(String(160))
    kind = col(String(30), default="product_page", nullable=False)
    __table_args__ = (UniqueConstraint("source_url", "version"),)


class DocumentModel(Base):
    __tablename__ = "document_models"
    document_id = col(ForeignKey("documents.id"), primary_key=True)
    model_id = col(ForeignKey("product_models.id"), primary_key=True)


class Chunk(Entity, Base):
    __tablename__ = "document_chunks"
    document_id = col(ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    text = col(Text, nullable=False)
    page = col(Integer)
    section = col(String(200))
    embedding = col(JSON, nullable=False)
    embedding_model = col(String(120), nullable=False)
    # PostgreSQL migration additionally creates embedding_vector vector(768).


class ChatSession(Entity, Base):
    __tablename__ = "chat_sessions"
    customer_id = col(ForeignKey("customers.id"), index=True, nullable=False)
    customer_product_id = col(ForeignKey("customer_products.id"), nullable=False)
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)


class ChatMessage(Entity, Base):
    __tablename__ = "chat_messages"
    session_id = col(ForeignKey("chat_sessions.id"), index=True, nullable=False)
    role = col(String(20), nullable=False)
    content = col(Text, nullable=False)
    sources = col(JSON, default=list, nullable=False)
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)


class SLARule(Entity, Base):
    __tablename__ = "sla_rules"
    severity = col(String(20), unique=True, nullable=False)
    response_minutes = col(Integer, nullable=False)
    resolution_minutes = col(Integer, nullable=False)
    timezone = col(String(80), default="Asia/Kolkata", nullable=False)
    weekdays = col(JSON, default=lambda: [0, 1, 2, 3, 4], nullable=False)
    start_hour = col(Integer, default=9, nullable=False)
    end_hour = col(Integer, default=17, nullable=False)
    official = col(Boolean, default=False, nullable=False)
    escalation_minutes = col(Integer, default=60, nullable=False)


class IssueCategory(Base):
    __tablename__ = "issue_categories"
    name = col(String(60), primary_key=True)
    enabled = col(Boolean, default=True, nullable=False)


class Ticket(Entity, Base):
    __tablename__ = "tickets"
    number = col(String(40), unique=True, nullable=False)
    customer_id = col(ForeignKey("customers.id"), index=True, nullable=False)
    customer_product_id = col(ForeignKey("customer_products.id"), nullable=False)
    category = col(ForeignKey("issue_categories.name"), nullable=False)
    severity = col(String(20), nullable=False)
    description = col(Text, nullable=False)
    approved_summary = col(Text)
    status = col(String(30), default="Open", nullable=False)
    idempotency_key = col(Uuid(as_uuid=False), nullable=False)
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)
    response_due_at = col(DateTime(timezone=True))
    resolution_due_at = col(DateTime(timezone=True))
    responded_at = col(DateTime(timezone=True))
    resolved_at = col(DateTime(timezone=True))
    sla_official = col(Boolean, default=False, nullable=False)
    escalation_minutes = col(Integer)
    __table_args__ = (UniqueConstraint("customer_id", "idempotency_key"),)


class TicketImage(Entity, Base):
    __tablename__ = "ticket_images"
    customer_id = col(ForeignKey("customers.id"), nullable=False, index=True)
    ticket_id = col(ForeignKey("tickets.id"), index=True)
    storage_path = col(Text, nullable=False)
    name = col(String(180), nullable=False)
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)


class TicketEvent(Entity, Base):
    __tablename__ = "ticket_events"
    ticket_id = col(ForeignKey("tickets.id"), index=True, nullable=False)
    status = col(String(30), nullable=False)
    note = col(Text, nullable=False)
    actor_id = col(Uuid(as_uuid=False), nullable=False)
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)


class EmailEvent(Entity, Base):
    __tablename__ = "email_events"
    ticket_id = col(ForeignKey("tickets.id"), nullable=False, index=True)
    state = col(String(30), default="pending", nullable=False)
    attempts = col(Integer, default=0, nullable=False)
    next_attempt_at = col(DateTime(timezone=True), default=utcnow, nullable=False)
    error = col(String(100))
    delivered_at = col(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("ticket_id"),)


class SyncEvent(Entity, Base):
    __tablename__ = "sync_events"
    source = col(String(30), nullable=False)
    record_id = col(String(120))
    status = col(String(30), nullable=False)
    error = col(String(100))
    last_synced_at = col(DateTime(timezone=True), default=utcnow, nullable=False)


class AuditEvent(Entity, Base):
    __tablename__ = "audit_events"
    actor_id = col(Uuid(as_uuid=False))
    action = col(String(100), nullable=False)
    resource_id = col(String(120))
    created_at = col(DateTime(timezone=True), default=utcnow, nullable=False)
