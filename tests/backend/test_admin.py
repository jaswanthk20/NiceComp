from datetime import timedelta
from sqlalchemy.orm import Session
from app.models import Ticket, utcnow
from app.sla_service import process_escalations
from conftest import ticket_payload


def test_sla_escalation_idempotent(client, customer, database):
    result = client.post("/tickets", headers=customer, json=ticket_payload(client, customer)).json()
    with Session(database) as db:
        ticket = db.get(Ticket, result["id"])
        ticket.response_due_at = utcnow() - timedelta(hours=5)
        ticket.resolution_due_at = utcnow() + timedelta(hours=5)
        db.flush()
        assert process_escalations(db) == 1
        assert process_escalations(db) == 0


def test_admin_warranty_evidence_required(client, admin, customer):
    product = client.get("/products", headers=customer).json()[0]
    response = client.put(
        "/admin/warranties/" + product["id"],
        headers=admin,
        json={
            "starts_on": "2026-01-01",
            "ends_on": "2027-01-01",
            "basis": "manual",
            "evidence": "Company verified written serial warranty.",
        },
    )
    assert response.status_code == 200
    assert (
        client.get("/products/" + product["id"], headers=customer).json()["warranty"]["basis"]
        == "manual"
    )


def test_admin_receipt_import_private(client, admin, customer, other):
    product = client.get("/products", headers=customer).json()[0]
    order = client.get("/purchases/" + product["purchase_id"], headers=customer).json()
    link = client.get("/receipts/" + order["receipts"][0]["id"] + "/url", headers=customer).json()[
        "url"
    ]
    raw = client.get(link).content
    result = client.post(
        "/admin/receipts/" + product["purchase_id"],
        headers=admin,
        files={"file": ("receipt.pdf", raw, "application/pdf")},
    )
    assert result.status_code == 201
    receipt = result.json()["id"]
    assert client.get("/receipts/" + receipt + "/url", headers=other).status_code == 404


def test_admin_sla_invalid_calendar(client, admin):
    response = client.put(
        "/admin/sla",
        headers=admin,
        json={
            "severity": "High",
            "response_minutes": 60,
            "resolution_minutes": 30,
            "weekdays": [],
            "start_hour": 17,
            "end_hour": 9,
            "official": True,
            "escalation_minutes": 60,
        },
    )
    assert response.status_code == 422
