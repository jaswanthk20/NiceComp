from datetime import date
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

Severity = Literal["Critical", "High", "Medium", "Low"]
Status = Literal[
    "Open", "Acknowledged", "In Progress", "Waiting for Customer", "Resolved", "Closed"
]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ChatInput(Input):
    customer_product_id: UUID
    session_id: UUID | None = None
    question: str = Field(min_length=2, max_length=2000)


class TicketInput(Input):
    customer_product_id: UUID
    category: str = Field(max_length=60)
    severity: Severity
    description: str = Field(min_length=10, max_length=6000)
    approved_summary: str | None = Field(default=None, max_length=4000)
    image_ids: list[UUID] = Field(default_factory=list, max_length=6)
    idempotency_key: UUID


class StatusInput(Input):
    status: Status
    note: str = Field(min_length=1, max_length=2000)


class SLAInput(Input):
    severity: Severity
    response_minutes: int = Field(gt=0, le=525600)
    resolution_minutes: int = Field(gt=0, le=1051200)
    timezone: str = "Asia/Kolkata"
    weekdays: list[int] = Field(min_length=1, max_length=7)
    start_hour: int = Field(ge=0, le=23)
    end_hour: int = Field(ge=1, le=24)
    official: bool = False
    escalation_minutes: int = Field(gt=0, le=43200)

    @field_validator("timezone")
    @classmethod
    def zone(cls, value):
        try:
            ZoneInfo(value)
        except Exception:
            raise ValueError("Unknown timezone")
        return value

    @model_validator(mode="after")
    def calendar(self):
        if (
            self.start_hour >= self.end_hour
            or any(x < 0 or x > 6 for x in self.weekdays)
            or len(set(self.weekdays)) != len(self.weekdays)
        ):
            raise ValueError("Invalid business hours")
        if self.resolution_minutes < self.response_minutes:
            raise ValueError("Resolution cannot precede response")
        return self


class MappingInput(Input):
    user_id: UUID
    customer_id: UUID


class WarrantyInput(Input):
    starts_on: date
    ends_on: date
    basis: Literal["purchase_policy", "explicit_pos", "serial", "manual"]
    evidence: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def dates(self):
        if self.ends_on < self.starts_on:
            raise ValueError("End date precedes start date")
        return self


class CategoryInput(Input):
    name: str = Field(min_length=2, max_length=60)
    enabled: bool = True
