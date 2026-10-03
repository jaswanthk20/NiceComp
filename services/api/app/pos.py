"""Authenticated connectors. Odoo activation requires verified deployment-specific field mapping."""

import csv
import io
import json
from datetime import date
from pathlib import Path
from typing import Protocol
import httpx
from pydantic import Field
from sqlalchemy import select
from .config import settings
from .observability import event
from .schemas import Input
from .models import (
    Customer,
    ProductModel,
    Purchase,
    PurchaseItem,
    OwnedProduct,
    Warranty,
    SyncEvent,
    utcnow,
)


class ExportRow(Input):
    customer_id: str = Field(min_length=1, max_length=120)
    customer_name: str = Field(min_length=1, max_length=160)
    customer_email: str = Field(max_length=254)
    order_id: str = Field(min_length=1, max_length=120)
    invoice_number: str = Field(min_length=1, max_length=120)
    purchased_on: date
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    amount: float | None = Field(default=None, ge=0)
    payment_status: str | None = None
    line_id: str
    model_source_id: str
    quantity: int = Field(gt=0, le=10000)
    asset_id: str
    serial: str | None = None
    warranty_start: date | None = None
    warranty_end: date | None = None
    warranty_evidence: str | None = None


class POSConnector(Protocol):
    def getCustomer(self, customer_id: str): ...
    def getCustomerPurchases(self, customer_id: str): ...
    def getPurchase(self, purchase_id: str): ...
    def getReceipt(self, purchase_id: str): ...
    def getPurchasedProducts(self, customer_id: str): ...
    def getWarrantyInformation(self, asset_id: str): ...
    def syncCustomers(self): ...
    def syncProducts(self): ...
    def syncPurchases(self) -> list[ExportRow]: ...


class CSVImportConnector:
    def __init__(self, data: bytes):
        if len(data) > 5_000_000:
            raise ValueError("Export too large")
        text = data.decode("utf-8-sig")
        raw = (
            json.loads(text)
            if text.lstrip().startswith("[")
            else list(csv.DictReader(io.StringIO(text)))
        )
        if not isinstance(raw, list) or len(raw) > 10000:
            raise ValueError("Export must contain at most 10,000 rows")
        self.rows = [
            ExportRow.model_validate(
                {
                    k: (
                        None
                        if v == ""
                        and k
                        in (
                            "amount",
                            "serial",
                            "payment_status",
                            "warranty_start",
                            "warranty_end",
                            "warranty_evidence",
                        )
                        else v
                    )
                    for k, v in r.items()
                }
            )
            for r in raw
        ]

    def getCustomer(self, customer_id):
        return next((r for r in self.rows if r.customer_id == customer_id), None)

    def getCustomerPurchases(self, customer_id):
        return [r for r in self.rows if r.customer_id == customer_id]

    def getPurchase(self, purchase_id):
        return [r for r in self.rows if r.order_id == purchase_id]

    def getReceipt(self, purchase_id):
        return None  # Receipt files require separate authorized import.

    def getPurchasedProducts(self, customer_id):
        return self.getCustomerPurchases(customer_id)

    def getWarrantyInformation(self, asset_id):
        return next((r for r in self.rows if r.asset_id == asset_id), None)

    def syncCustomers(self):
        return {r.customer_id: r for r in self.rows}.values()

    def syncProducts(self):
        return sorted({r.model_source_id for r in self.rows})

    def syncPurchases(self):
        return self.rows


class DevelopmentTestConnector(CSVImportConnector):
    def __init__(self, data):
        if settings().app_env not in ("development", "test"):
            raise ValueError("Development connector disabled")
        super().__init__(data)


class OdooConnector:
    """Odoo 19 JSON-2; no presumed private models, fields, report or warranty endpoint."""

    def __init__(self):
        cfg = settings()
        if not cfg.odoo_api_verified or not cfg.odoo_mapping_file or not cfg.odoo_api_key:
            raise ValueError(
                "Odoo API entitlement, credentials and /doc field mapping must be verified first"
            )
        if not cfg.odoo_base_url.startswith("https://"):
            raise ValueError("Odoo requires HTTPS")
        self.mapping = json.loads(Path(cfg.odoo_mapping_file).read_text())
        if self.mapping.get("api_version") != "19-json-2":
            raise ValueError("Unsupported Odoo API mapping")

    def call(self, key, domain=None):
        cfg = settings()
        spec = self.mapping["resources"][key]
        response = httpx.post(
            cfg.odoo_base_url.rstrip("/") + "/json/2/" + spec["model"] + "/search_read",
            headers={
                "Authorization": "Bearer " + cfg.odoo_api_key,
                "X-Odoo-Database": cfg.odoo_database,
            },
            json={"domain": domain or [], "fields": spec["fields"], "limit": 10001},
            timeout=30,
        )
        response.raise_for_status()
        rows = response.json()
        if len(rows) > 10000:
            raise ValueError(
                "Export exceeds batch limit; configure incremental domain before activation"
            )
        return rows

    def getCustomer(self, customer_id):
        return self.call("customers", [["id", "=", int(customer_id)]])

    def getCustomerPurchases(self, customer_id):
        return self.call("purchases", [[self.mapping["customer_field"], "=", int(customer_id)]])

    def getPurchase(self, purchase_id):
        return self.call("purchases", [["id", "=", int(purchase_id)]])

    def getReceipt(self, purchase_id):
        if "receipts" not in self.mapping["resources"]:
            return None
        return self.call(
            "receipts", [[self.mapping["receipt_purchase_field"], "=", int(purchase_id)]]
        )

    def getPurchasedProducts(self, customer_id):
        return self.getCustomerPurchases(customer_id)

    def getWarrantyInformation(self, asset_id):
        if "warranties" not in self.mapping["resources"]:
            return None
        return self.call("warranties", [[self.mapping["warranty_asset_field"], "=", asset_id]])

    def syncCustomers(self):
        return self.call("customers")

    def syncProducts(self):
        return self.call("products")

    def syncPurchases(self):
        # Company-approved export/view must yield one row per serialized asset.
        mapping = self.mapping["canonical_export_fields"]
        return [
            ExportRow.model_validate(
                {canonical: row.get(source) for canonical, source in mapping.items()}
            )
            for row in self.call("canonical_export")
        ]


def synchronize(db, connector: POSConnector, source="csv"):
    rows = connector.syncPurchases()
    for row in rows:
        customer = db.scalar(
            select(Customer).where(Customer.source == source, Customer.source_id == row.customer_id)
        )
        if not customer:
            customer = Customer(
                source=source,
                source_id=row.customer_id,
                name=row.customer_name,
                email=row.customer_email,
            )
            db.add(customer)
            db.flush()
        else:
            customer.name = row.customer_name
            customer.email = row.customer_email
        model = db.scalar(
            select(ProductModel).where(
                ProductModel.source == source, ProductModel.source_id == row.model_source_id
            )
        )
        if not model:
            raise ValueError("Unknown product mapping: import and verify product models first")
        order = db.scalar(
            select(Purchase).where(Purchase.source == source, Purchase.source_id == row.order_id)
        )
        if not order:
            order = Purchase(
                customer_id=customer.id,
                source=source,
                source_id=row.order_id,
                invoice_number=row.invoice_number,
                purchased_on=row.purchased_on,
                currency=row.currency,
            )
            db.add(order)
            db.flush()
        if order.customer_id != customer.id:
            raise ValueError("Source order ownership conflict")
        order.amount = row.amount
        order.payment_status = row.payment_status
        order.last_synced_at = utcnow()
        item = db.scalar(
            select(PurchaseItem).where(
                PurchaseItem.purchase_id == order.id, PurchaseItem.source_line_id == row.line_id
            )
        )
        if not item:
            item = PurchaseItem(
                purchase_id=order.id,
                model_id=model.id,
                source_line_id=row.line_id,
                quantity=row.quantity,
            )
            db.add(item)
            db.flush()
        if item.model_id != model.id:
            raise ValueError("Source line model conflict")
        item.quantity = row.quantity
        asset = db.scalar(
            select(OwnedProduct).where(
                OwnedProduct.purchase_item_id == item.id,
                OwnedProduct.source_asset_id == row.asset_id,
            )
        )
        if not asset:
            asset = OwnedProduct(
                customer_id=customer.id,
                model_id=model.id,
                purchase_item_id=item.id,
                source_asset_id=row.asset_id,
                serial=row.serial,
            )
            db.add(asset)
            db.flush()
        if row.warranty_start and row.warranty_end and row.warranty_evidence:
            if row.warranty_end < row.warranty_start:
                raise ValueError("Invalid warranty dates")
            warranty = db.scalar(select(Warranty).where(Warranty.customer_product_id == asset.id))
            if not warranty:
                warranty = Warranty(
                    customer_product_id=asset.id,
                    basis="explicit_pos",
                    evidence=row.warranty_evidence,
                )
                db.add(warranty)
            if warranty.basis != "manual":
                warranty.starts_on = row.warranty_start
                warranty.ends_on = row.warranty_end
                warranty.evidence = row.warranty_evidence
        db.add(SyncEvent(source=source, record_id=row.order_id, status="synced"))
    db.flush()
    event("pos.synchronized", source=source, records=len(rows))
    return len(rows)
