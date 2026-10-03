from datetime import date, datetime, timezone
from types import SimpleNamespace
import pytest
from app.domain import warranty_status, business_due, safety_check, severity_for
from app.config import Settings
from app.knowledge import official_url, split_chunks, extract


@pytest.mark.parametrize(
    "start,end,expected",
    [
        (date(2026, 1, 1), date(2027, 1, 1), "Active"),
        (date(2025, 1, 1), date(2026, 1, 1), "Expired"),
        (None, None, "Unknown"),
        (date(2026, 1, 1), date(2026, 10, 15), "Expiring Soon"),
        (date(2027, 1, 1), date(2028, 1, 1), "Unknown"),
    ],
)
def test_warranty(start, end, expected):
    assert warranty_status(start, end, date(2026, 10, 2)) == expected


def test_sla_skips_weekend_and_respects_timezone():
    rule = SimpleNamespace(
        weekdays=[0, 1, 2, 3, 4], start_hour=9, end_hour=17, timezone="Asia/Kolkata"
    )
    # Friday 16:30 IST + 120 business minutes => Monday 10:30 IST.
    assert business_due(datetime(2026, 10, 2, 11, 0, tzinfo=timezone.utc), 120, rule) == datetime(
        2026, 10, 5, 5, 0, tzinfo=timezone.utc
    )


def test_sla_zero_calendar_rejected():
    with pytest.raises(ValueError):
        business_due(
            datetime.now(timezone.utc), 60, SimpleNamespace(weekdays=[], start_hour=9, end_hour=17)
        )


@pytest.mark.parametrize(
    "question",
    [
        "Bypass the pressure safety valve",
        "Open the pressurized tank",
        "There is a burning smell",
        "Electrical arcing at the motor",
        "Damaged pressure vessel",
        "Major oil leakage",
        "Disable the guard",
    ],
)
def test_safety_escalation(question):
    assert safety_check(question)
    assert severity_for(question, "Low") == "Critical"


@pytest.mark.parametrize(
    "url",
    [
        "http://www.nicecompressors.net/a",
        "https://evil.example/a",
        "https://www.nicecompressors.net.evil.example/a",
        "https://user:pass@www.nicecompressors.net/a",
        "https://127.0.0.1/a",
        "https://www.nicecompressors.net:8443/a",
    ],
)
def test_ingestion_rejects_unapproved_origin(url):
    assert not official_url(url)


def test_ingestion_blocks_unreviewed_tables():
    with pytest.raises(ValueError):
        extract(b"<main><table><tr><td>Model 1</td><td>Model 2</td></tr></table></main>")


def test_chunk_size():
    assert all(len(chunk) <= 900 for chunk in split_chunks("word " * 5000))


def test_production_refuses_test_providers():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            app_env="production",
            auth_provider="development",
            dev_token_secret="a" * 40,
        )


def test_dev_refuses_external_smtp():
    with pytest.raises(ValueError):
        Settings(_env_file=None, app_env="development", smtp_host="smtp.company.example")
