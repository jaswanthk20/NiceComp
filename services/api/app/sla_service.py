"""Idempotent internal escalation flags on the ticket timeline."""

from datetime import timezone, timedelta
from sqlalchemy import select
from .models import Ticket, TicketEvent, utcnow

SYSTEM_ACTOR = "00000000-0000-4000-8000-000000000001"


def process_escalations(db, now=None):
    now = now or utcnow()
    count = 0
    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.status.notin_(["Resolved", "Closed"]), Ticket.escalation_minutes.is_not(None))
        .with_for_update(skip_locked=True)
    ).all()
    for ticket in tickets:
        for label, due, done in [
            ("Response", ticket.response_due_at, ticket.responded_at),
            ("Resolution", ticket.resolution_due_at, ticket.resolved_at),
        ]:
            if due and not done:
                due = due.replace(tzinfo=due.tzinfo or timezone.utc)
                note = f"{label} target overdue. Escalated for support review."
                if now >= due + timedelta(minutes=ticket.escalation_minutes) and not db.scalar(
                    select(TicketEvent.id).where(
                        TicketEvent.ticket_id == ticket.id, TicketEvent.note == note
                    )
                ):
                    db.add(
                        TicketEvent(
                            ticket_id=ticket.id,
                            status=ticket.status,
                            note=note,
                            actor_id=SYSTEM_ACTOR,
                        )
                    )
                    count += 1
    db.flush()
    return count
