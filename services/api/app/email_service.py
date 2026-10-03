from datetime import timedelta
from email.message import EmailMessage
from typing import Protocol
import smtplib
import ssl
from sqlalchemy import select
from .config import settings
from .models import (
    EmailEvent,
    Ticket,
    Customer,
    OwnedProduct,
    ProductModel,
    PurchaseItem,
    Purchase,
    Warranty,
    TicketImage,
    utcnow,
)
from .domain import warranty_status
from .observability import event as log_event


class EmailProvider(Protocol):
    def send(self, message: EmailMessage): ...


class MailpitEmailProvider:
    def send(self, message):
        cfg = settings()
        # Never use a real recipient in local review, even if accidentally configured.
        if "To" in message:
            del message["To"]
        message["To"] = "support@nicecomp.test"
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=15) as smtp:
            smtp.send_message(message)


class SMTPEmailProvider:
    def send(self, message):
        cfg = settings()
        if cfg.app_env != "production" or not cfg.production_recipient_confirmed:
            raise ValueError("Production SMTP is not approved")
        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if cfg.smtp_username:
                smtp.login(cfg.smtp_username, cfg.smtp_password)
            smtp.send_message(message)


def build_email(db, ticket):
    cfg = settings()
    customer = db.get(Customer, ticket.customer_id)
    asset = db.get(OwnedProduct, ticket.customer_product_id)
    model = db.get(ProductModel, asset.model_id)
    item = db.get(PurchaseItem, asset.purchase_item_id)
    order = db.get(Purchase, item.purchase_id)
    warranty = db.scalar(select(Warranty).where(Warranty.customer_product_id == asset.id))
    message = EmailMessage()
    message["From"] = cfg.smtp_from_email
    message["To"] = (
        cfg.support_owner_email if cfg.app_env == "production" else "support@nicecomp.test"
    )
    message["Subject"] = (
        f"[NICE Support][{ticket.severity.upper()}][Ticket {ticket.number}] {model.name} - {ticket.category}"
    )
    message["Message-ID"] = f"<{ticket.id}@nicecomp.support>"
    sla = str(ticket.response_due_at) if ticket.sla_official else "No official SLA configured"
    message.set_content(f"""Ticket: {ticket.number}
Priority: {ticket.severity}
Response target: {sla}
Customer: {customer.name}
Email: {customer.email}
Phone: {customer.phone or "Unavailable"}
Product/model: {model.name}
Serial: {asset.serial or "Unavailable"}
Purchase date: {order.purchased_on}
Warranty: {warranty_status(warranty.starts_on, warranty.ends_on) if warranty else "Unknown"}
Category: {ticket.category}
Problem: {ticket.description}
Customer-approved chat context: {ticket.approved_summary or "Not shared"}
Created: {ticket.created_at}
Review securely: {cfg.web_base_url}/ticket/{ticket.id}
""")
    # Authenticated admin review avoids expiring photo links in email and never makes photos public.
    count = len(db.scalars(select(TicketImage).where(TicketImage.ticket_id == ticket.id)).all())
    message.set_content(
        message.get_content()
        + f"Photos: {count}. Sign in to the support console to view the private images.\n"
    )
    return message


def deliver_pending(db, provider=None):
    provider = provider or (
        MailpitEmailProvider() if settings().email_provider == "mailpit" else SMTPEmailProvider()
    )
    events = db.scalars(
        select(EmailEvent)
        .where(EmailEvent.state.in_(["pending", "retry"]), EmailEvent.next_attempt_at <= utcnow())
        .with_for_update(skip_locked=True)
        .limit(20)
    ).all()
    for event in events:
        event.attempts += 1
        try:
            provider.send(build_email(db, db.get(Ticket, event.ticket_id)))
            event.state = "sent"
            event.delivered_at = utcnow()
            event.error = None
        except Exception:
            event.state = "retry" if event.attempts < 8 else "failed"
            event.error = "Email delivery unavailable"
            event.next_attempt_at = utcnow() + timedelta(seconds=min(3600, 30 * 2**event.attempts))
        log_event(
            "email.delivery", ticket_id=event.ticket_id, state=event.state, attempts=event.attempts
        )
    db.flush()
    return len(events)
