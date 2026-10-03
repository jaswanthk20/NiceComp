"""Explicit development fixtures. Never runs at API startup or in production."""

from datetime import date, timedelta
from pathlib import Path
import io
import json
import os
import hashlib
import httpx
from sqlalchemy import select
from reportlab.pdfgen import canvas
from .config import settings
from .db import engine, session_factory
from .models import *
from .auth import hash_password
from .storage import storage
from .knowledge import index_document

ROOT = Path(__file__).resolve().parents[3]
DEMO_CUSTOMER = "11111111-1111-4111-8111-111111111111"
DEMO_ADMIN = "22222222-2222-4222-8222-222222222222"
OTHER_USER = "33333333-3333-4333-8333-333333333333"


def seed(db, password="Review-Only-2026!"):
    if settings().app_env not in ("development", "test"):
        raise RuntimeError("Development seed refused")
    if db.scalar(select(Profile).where(Profile.id == DEMO_CUSTOMER)):
        return
    customers = []
    for index, (user_id, name, email, role) in enumerate(
        [
            (DEMO_CUSTOMER, "TEST CUSTOMER", "customer@nicecomp.test", "customer"),
            (DEMO_ADMIN, "TEST ADMIN", "admin@nicecomp.test", "admin"),
            (OTHER_USER, "OTHER TEST CUSTOMER", "other@nicecomp.test", "customer"),
        ]
    ):
        customer = Customer(name=name, email=email, source="development", source_id=f"TEST-{index}")
        db.add(customer)
        db.flush()
        customers.append(customer)
        db.add(
            Profile(
                id=user_id,
                customer_id=customer.id if role == "customer" else None,
                display_name=name,
                role=role,
            )
        )
        db.flush()
        if settings().auth_provider == "development":
            db.add(
                DevCredential(user_id=user_id, email=email, password_hash=hash_password(password))
            )
    product = Product(
        family="Rotary Screw Compressors",
        name="Rotary screw compressor",
        official_url="https://www.nicecompressors.net/rotary-screw-compressor",
    )
    db.add(product)
    db.flush()
    model = ProductModel(
        product_id=product.id, name="ECO 10A", source="development", source_id="TEST-MODEL-ECO10A"
    )
    db.add(model)
    db.flush()
    for index, customer in enumerate([customers[0], customers[2]]):
        order = Purchase(
            customer_id=customer.id,
            source="development",
            source_id=f"TEST-INVOICE-{index}",
            invoice_number=f"TEST INVOICE {index + 1:03d}",
            purchased_on=date.today() - timedelta(days=20),
            currency="INR",
            amount=100,
            payment_status="TEST PAID",
        )
        db.add(order)
        db.flush()
        line = PurchaseItem(
            purchase_id=order.id,
            model_id=model.id,
            source_line_id="TEST-LINE",
            quantity=1,
            amount=100,
        )
        db.add(line)
        db.flush()
        asset = OwnedProduct(
            customer_id=customer.id,
            model_id=model.id,
            purchase_item_id=line.id,
            serial=f"TEST-SERIAL-{index + 1:03d}",
            source_asset_id="TEST-ASSET",
        )
        db.add(asset)
        db.flush()
        db.add(
            Warranty(
                customer_product_id=asset.id,
                starts_on=date.today() - timedelta(days=20),
                ends_on=date.today() + timedelta(days=90),
                basis="explicit_pos",
                evidence="SYNTHETIC DEVELOPMENT FIXTURE. Not company warranty policy.",
            )
        )
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.setTitle("TEST RECEIPT — SYNTHETIC")
        for y, txt in [
            (780, "TEST RECEIPT - NOT A REAL INVOICE"),
            (730, customer.name),
            (690, order.invoice_number),
            (650, "ECO 10A | Quantity 1 | TEST amount INR 100"),
            (610, "Synthetic demonstration data only. Not evidence of purchase."),
        ]:
            pdf.drawString(45, y, txt)
        pdf.save()
        path = f"{customer.id}/receipts/{order.id}.pdf"
        storage().put(path, buffer.getvalue(), "application/pdf")
        db.add(Receipt(purchase_id=order.id, storage_path=path, name="TEST RECEIPT.pdf"))
    for category in [
        "Performance",
        "Pressure",
        "Electrical",
        "Motor",
        "Oil/Lubrication",
        "Noise/Vibration",
        "Leak",
        "Overheating",
        "Maintenance",
        "Spare Parts",
        "Other",
    ]:
        db.add(IssueCategory(name=category))
    for severity, minutes in [("Critical", 60), ("High", 240), ("Medium", 480), ("Low", 960)]:
        db.add(
            SLARule(
                severity=severity,
                response_minutes=minutes,
                resolution_minutes=minutes * 4,
                weekdays=[0, 1, 2, 3, 4],
                start_hour=9,
                end_hour=17,
                timezone="Asia/Kolkata",
                official=False,
                escalation_minutes=60,
            )
        )
    for source in json.loads(
        (ROOT / "knowledge/reviewed-excerpts.json").read_text(encoding="utf-8")
    ):
        doc = Document(
            title=source["title"],
            source_url=source["source_url"],
            version=source["version"],
            family=source["family"],
            sha256=hashlib.sha256(source["text"].encode()).hexdigest(),
            kind=source["kind"],
            approved=True,
            active=True,
        )
        db.add(doc)
        db.flush()
        db.add(DocumentModel(document_id=doc.id, model_id=model.id))
        db.flush()
        index_document(db, doc, [(None, source["text"])])
    db.flush()


def seed_supabase_auth(password):
    cfg = settings()
    if cfg.app_env == "production":
        raise RuntimeError("Development seed refused")
    for user_id, email in [
        (DEMO_CUSTOMER, "customer@nicecomp.test"),
        (DEMO_ADMIN, "admin@nicecomp.test"),
        (OTHER_USER, "other@nicecomp.test"),
    ]:
        response = httpx.post(
            cfg.supabase_url + "/auth/v1/admin/users",
            headers={
                "apikey": cfg.supabase_service_role_key,
                "Authorization": "Bearer " + cfg.supabase_service_role_key,
            },
            json={"id": user_id, "email": email, "password": password, "email_confirm": True},
            timeout=20,
        )
        if response.status_code not in (200, 201, 422):
            response.raise_for_status()


if __name__ == "__main__":
    if settings().app_env == "production":
        raise SystemExit("Production seed refused")
    if settings().database_url.startswith("sqlite"):
        Base.metadata.create_all(engine())
    password = os.environ.get("DEMO_PASSWORD", "Review-Only-2026!")
    with session_factory()() as db:
        seed(db, password)
        db.commit()
    if settings().auth_provider == "supabase":
        seed_supabase_auth(password)
    print(
        "Development fixtures ready. Accounts: customer@nicecomp.test / admin@nicecomp.test. See LOCAL_DEMO.md."
    )
