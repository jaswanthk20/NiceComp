import json
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import pytest
from app.models import ProductModel, Purchase
from app.pos import CSVImportConnector, OdooConnector, synchronize


def fixture_row():
    return {
        "customer_id": "TEST-CUSTOMER",
        "customer_name": "TEST CUSTOMER",
        "customer_email": "test@example.test",
        "order_id": "TEST-ORDER",
        "invoice_number": "TEST INVOICE",
        "purchased_on": "2026-10-02",
        "currency": "INR",
        "amount": 10,
        "line_id": "TEST-LINE",
        "model_source_id": "TEST-MODEL",
        "quantity": 1,
        "asset_id": "TEST-ASSET",
        "serial": "TEST-SERIAL",
    }


def test_sync_idempotent(database):
    with Session(database) as db:
        original = db.scalar(select(ProductModel))
        db.add(
            ProductModel(
                product_id=original.product_id,
                name="TEST PRODUCT",
                source="csv",
                source_id="TEST-MODEL",
            )
        )
        db.flush()
        connector = CSVImportConnector(json.dumps([fixture_row()]).encode())
        assert synchronize(db, connector) == 1
        assert synchronize(db, connector) == 1
        assert (
            db.scalar(select(func.count()).select_from(Purchase).where(Purchase.source == "csv"))
            == 1
        )


def test_missing_product_mapping_rolls_back(client, admin):
    response = client.post(
        "/admin/sync/import",
        headers=admin,
        files={"file": ("test.json", json.dumps([fixture_row()]).encode(), "application/json")},
    )
    assert response.json()["status"] == "failed"


def test_odoo_unverified_fails_closed():
    with pytest.raises(ValueError):
        OdooConnector()


def test_odoo_api_failure_recorded(client, admin, monkeypatch):
    class Failed:
        def syncPurchases(self):
            raise ConnectionError("unavailable")

    monkeypatch.setattr("app.admin_routes.OdooConnector", Failed)
    response = client.post("/admin/sync/odoo", headers=admin)
    assert response.json()["status"] == "failed"
    assert client.get("/admin/events", headers=admin).json()["sync"][0]["status"] == "failed"


def test_invalid_csv_rejected():
    with pytest.raises(Exception):
        CSVImportConnector(b"foo,bar\n1,2")
