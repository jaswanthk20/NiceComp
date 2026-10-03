from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re


def warranty_status(start: date | None, end: date | None, today: date | None = None):
    today = today or date.today()
    if not start or not end or start > today or end < start:
        return "Unknown"
    if end < today:
        return "Expired"
    if (end - today).days <= 30:
        return "Expiring Soon"
    return "Active"


def business_due(start: datetime, minutes: int, rule):
    if minutes <= 0 or not rule.weekdays or rule.start_hour >= rule.end_hour:
        raise ValueError("Invalid SLA calendar")
    current = start.astimezone(ZoneInfo(rule.timezone))
    remaining = minutes * 60
    for _ in range(4000):
        opening = current.replace(hour=rule.start_hour, minute=0, second=0, microsecond=0)
        closing = (
            opening.replace(hour=0) + timedelta(days=1)
            if rule.end_hour == 24
            else opening.replace(hour=rule.end_hour)
        )
        if current.weekday() not in rule.weekdays or current >= closing:
            current = (current + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            continue
        current = max(current, opening)
        available = (
            closing.astimezone(timezone.utc) - current.astimezone(timezone.utc)
        ).total_seconds()
        if remaining <= available:
            return current.astimezone(timezone.utc) + timedelta(seconds=remaining)
        remaining -= available
        current = closing
    raise ValueError("SLA calendar exceeds supported horizon")


HAZARDS = re.compile(
    r"smoke|burning\s+smell|arcing|severe\s+overheat|relief.{0,25}(fail|malfunction|stuck)|damaged.{0,20}(vessel|tank)|major.{0,15}oil.{0,15}leak|mechanical\s+failure|fire|sparks",
    re.I,
)
DANGEROUS = re.compile(
    r"bypass|disable.{0,25}(guard|protect|safety)|override|open.{0,30}(pressuri|tank|vessel)|increase.{0,30}(pressure|limit)|remove.{0,20}(guard|relief)|defeat.{0,20}(safety|switch)",
    re.I,
)
SAFETY_MESSAGE = (
    "Stop operation if it is safe to do so. Do not open pressurized components, bypass safety devices, or attempt repairs. "
    "Follow the official shutdown and isolation procedure for your machine and contact qualified Nice Compressors support. "
    "I cannot verify a shutdown procedure from the available documentation."
)


def safety_check(question):
    return SAFETY_MESSAGE if HAZARDS.search(question) or DANGEROUS.search(question) else None


def severity_for(description: str, requested: str):
    if HAZARDS.search(description) or DANGEROUS.search(description):
        return "Critical"
    return requested


TRANSITIONS = {
    "Open": {"Acknowledged", "In Progress"},
    "Acknowledged": {"In Progress", "Waiting for Customer"},
    "In Progress": {"Waiting for Customer", "Resolved"},
    "Waiting for Customer": {"In Progress", "Resolved"},
    "Resolved": {"Closed", "In Progress"},
    "Closed": set(),
}
