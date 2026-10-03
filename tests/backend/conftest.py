import os
import sys
from pathlib import Path
from uuid import uuid4
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api"))
os.environ.update(
    APP_ENV="test",
    AUTH_PROVIDER="development",
    STORAGE_PROVIDER="local",
    DEV_TOKEN_SECRET="test-secret-only-not-for-production-12345678",
    EMBEDDING_PROVIDER="development",
    CHAT_PROVIDER="extractive",
    DATABASE_URL="sqlite://",
    EMAIL_PROVIDER="mailpit",
)
from app.config import settings
from app.db import get_db
from app.models import Base
from app.seed import seed
from app.auth import limiter
from app.main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


@pytest.fixture
def database(tmp_path):
    os.environ["PRIVATE_STORAGE_DIR"] = str(tmp_path / "private")
    settings.cache_clear()
    limiter.hits.clear()
    e = create_engine(
        "sqlite:///" + str(tmp_path / "test.db"), connect_args={"check_same_thread": False}
    )
    from sqlalchemy import event

    @event.listens_for(e, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(e)
    with Session(e) as db:
        seed(db)
        db.commit()
    yield e
    e.dispose()


@pytest.fixture
def client(database):
    def override():
        with Session(database, expire_on_commit=False) as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def login(client, email="customer@nicecomp.test"):
    result = client.post(
        "/auth/development-login", json={"email": email, "password": "Review-Only-2026!"}
    )
    assert result.status_code == 200, result.text
    return {"Authorization": "Bearer " + result.json()["access_token"]}


@pytest.fixture
def customer(client):
    return login(client)


@pytest.fixture
def other(client):
    return login(client, "other@nicecomp.test")


@pytest.fixture
def admin(client):
    return login(client, "admin@nicecomp.test")


def ticket_payload(client, headers, **overrides):
    product = client.get("/products", headers=headers).json()[0]
    return {
        "customer_product_id": product["id"],
        "category": "Pressure",
        "severity": "High",
        "description": "Pressure drops during normal use. Please help.",
        "idempotency_key": str(uuid4()),
        "image_ids": [],
        **overrides,
    }
