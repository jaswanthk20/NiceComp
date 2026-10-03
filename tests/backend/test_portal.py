from uuid import uuid4
import pytest


def test_customer_login(client, customer):
    me = client.get("/me", headers=customer)
    assert me.status_code == 200
    assert me.json()["role"] == "customer"


def test_invalid_login(client):
    assert (
        client.post(
            "/auth/development-login", json={"email": "customer@nicecomp.test", "password": "bad"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize("path", ["/me", "/products", "/purchases", "/tickets", "/admin/tickets"])
def test_auth_required(client, path):
    assert client.get(path).status_code == 401


def test_forged_token_rejected(client):
    assert client.get("/me", headers={"Authorization": "Bearer forged"}).status_code == 401


def test_own_purchase_receipt_and_warranty(client, customer):
    product = client.get("/products", headers=customer).json()[0]
    assert product["warranty"]["status"] == "Active"
    order = client.get("/purchases/" + product["purchase_id"], headers=customer).json()
    receipt = order["receipts"][0]
    link = client.get("/receipts/" + receipt["id"] + "/url", headers=customer)
    assert link.status_code == 200
    assert link.json()["expires_in"] == 120
    file = client.get(link.json()["url"])
    assert file.status_code == 200
    assert file.content.startswith(b"%PDF-")


def test_receipt_renders_inside_app(client, customer):
    product = client.get("/products", headers=customer).json()[0]
    receipt = client.get("/purchases/" + product["purchase_id"], headers=customer).json()[
        "receipts"
    ][0]
    response = client.get("/receipts/" + receipt["id"] + "/pages", headers=customer)
    assert response.status_code == 200
    assert len(response.json()["pages"]) == 1
    assert client.get(response.json()["pages"][0]["url"]).headers["content-type"] == "image/jpeg"


def test_cross_customer_purchase_product_receipt(client, customer, other):
    product = client.get("/products", headers=other).json()[0]
    receipt = client.get("/purchases/" + product["purchase_id"], headers=other).json()["receipts"][
        0
    ]
    for path in [
        "/products/" + product["id"],
        "/purchases/" + product["purchase_id"],
        "/receipts/" + receipt["id"] + "/url",
        "/receipts/" + receipt["id"] + "/pages",
        "/chat/" + product["id"],
    ]:
        assert client.get(path, headers=customer).status_code == 404


@pytest.mark.parametrize(
    "path",
    ["/admin/tickets", "/admin/customers", "/admin/events", "/admin/documents", "/admin/sla"],
)
def test_admin_protected(client, customer, path):
    assert client.get(path, headers=customer).status_code == 403


def test_client_cannot_choose_customer_id(client, customer):
    assert (
        client.post(
            "/chat",
            headers=customer,
            json={
                "customer_id": str(uuid4()),
                "customer_product_id": str(uuid4()),
                "question": "hello",
            },
        ).status_code
        == 422
    )


def test_missing_mapping_is_explicit(client, customer, database):
    from sqlalchemy.orm import Session
    from app.models import Profile
    from app.seed import DEMO_CUSTOMER

    with Session(database) as db:
        db.get(Profile, DEMO_CUSTOMER).customer_id = None
        db.commit()
    assert client.get("/products", headers=customer).status_code == 403
