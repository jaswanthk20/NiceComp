import io
from datetime import timedelta
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models import Ticket, EmailEvent, SLARule, utcnow
from app.email_service import build_email, deliver_pending, MailpitEmailProvider
from conftest import ticket_payload


def photo():
    buf = io.BytesIO()
    Image.new("RGB", (80, 80), "blue").save(buf, "JPEG")
    return buf.getvalue()


def test_create_ticket_with_image_sla_and_outbox(client, customer, database):
    upload = client.post(
        "/images", headers=customer, files={"file": ("test.jpg", photo(), "image/jpeg")}
    )
    assert upload.status_code == 201, upload.text
    body = ticket_payload(client, customer, image_ids=[upload.json()["id"]])
    response = client.post("/tickets", headers=customer, json=body)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["number"].startswith("NC-")
    assert data["response_due_at"] is None
    detail = client.get("/tickets/" + data["id"], headers=customer).json()
    assert len(detail["events"]) == 1
    assert detail["events"][0]["created_at"].endswith(("+00:00", "Z"))
    assert len(detail["images"]) == 1
    assert detail["email_status"] == "pending"
    with Session(database) as db:
        ticket = db.get(Ticket, data["id"])
        assert ticket.response_due_at
        assert ticket.resolution_due_at > ticket.response_due_at


def test_ticket_idempotent_retry(client, customer, database):
    body = ticket_payload(client, customer)
    first = client.post("/tickets", headers=customer, json=body)
    second = client.post("/tickets", headers=customer, json=body)
    assert first.json()["id"] == second.json()["id"]
    with Session(database) as db:
        assert len(db.scalars(select(EmailEvent)).all()) == 1


def test_photo_content_validation(client, customer):
    assert (
        client.post(
            "/images", headers=customer, files={"file": ("fake.jpg", b"not an image", "image/jpeg")}
        ).status_code
        == 422
    )


def test_private_image_access(client, customer, other):
    image = client.post(
        "/images", headers=other, files={"file": ("test.jpg", photo(), "image/jpeg")}
    ).json()
    assert client.get("/images/" + image["id"] + "/url", headers=customer).status_code == 404
    assert (
        client.post(
            "/tickets",
            headers=customer,
            json=ticket_payload(client, customer, image_ids=[image["id"]]),
        ).status_code
        == 422
    )


def test_private_ticket_access(client, customer, other):
    ticket = client.post("/tickets", headers=other, json=ticket_payload(client, other)).json()
    assert client.get("/tickets/" + ticket["id"], headers=customer).status_code == 404


def test_dangerous_fault_forces_critical(client, customer):
    ticket = client.post(
        "/tickets",
        headers=customer,
        json=ticket_payload(
            client,
            customer,
            severity="Low",
            description="There is smoke and a burning smell from the motor.",
        ),
    ).json()
    assert ticket["severity"] == "Critical"


def test_official_sla_visible(client, customer, database):
    with Session(database) as db:
        db.scalar(select(SLARule).where(SLARule.severity == "High")).official = True
        db.commit()
    ticket = client.post("/tickets", headers=customer, json=ticket_payload(client, customer)).json()
    assert ticket["response_due_at"]
    assert ticket["sla_message"] is None


def test_status_timeline(client, customer, admin):
    ticket = client.post("/tickets", headers=customer, json=ticket_payload(client, customer)).json()
    path = "/admin/tickets/" + ticket["id"]
    assert (
        client.patch(
            path, headers=customer, json={"status": "Acknowledged", "note": "Attempt"}
        ).status_code
        == 403
    )
    assert (
        client.patch(
            path, headers=admin, json={"status": "Closed", "note": "Invalid transition"}
        ).status_code
        == 409
    )
    assert (
        client.patch(
            path, headers=admin, json={"status": "Acknowledged", "note": "Support is reviewing."}
        ).status_code
        == 200
    )
    detail = client.get("/tickets/" + ticket["id"], headers=customer).json()
    assert len(detail["events"]) == 2
    assert detail["ticket"]["status"] == "Acknowledged"


def test_email_contents_and_retry(client, customer, database):
    ticket = client.post(
        "/tickets",
        headers=customer,
        json=ticket_payload(client, customer, approved_summary="Customer reviewed this context."),
    ).json()

    class Failing:
        def send(self, message):
            raise OSError("SMTP down")

    class Captured:
        messages = []

        def send(self, message):
            self.messages.append(message)

    with Session(database) as db:
        message = build_email(db, db.get(Ticket, ticket["id"]))
        assert message["To"] == "support@nicecomp.test"
        assert "[HIGH]" in message["Subject"]
        assert ticket["number"] in message["Subject"]
        assert "TEST CUSTOMER" in message.get_content()
        assert "Customer reviewed this context" in message.get_content()
        assert "Sign in" in message.get_content()
        assert "No official SLA configured" in message.get_content()
        deliver_pending(db, Failing())
        event = db.scalar(select(EmailEvent))
        assert event.state == "retry"
        assert event.attempts == 1
        event.next_attempt_at = utcnow() - timedelta(seconds=1)
        db.flush()
        capture = Captured()
        deliver_pending(db, capture)
        assert event.state == "sent"
        assert len(capture.messages) == 1


def test_mailpit_forces_test_recipient(monkeypatch):
    from email.message import EmailMessage

    observed = []

    class SMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def send_message(self, message):
            observed.append(message["To"])

    monkeypatch.setattr("app.email_service.smtplib.SMTP", SMTP)
    message = EmailMessage()
    message["To"] = "real-company@example.com"
    message.set_content("test")
    MailpitEmailProvider().send(message)
    assert observed == ["support@nicecomp.test"]
