"""Durable outbox worker. Run alongside API; never send mail in request transactions."""

import time
import logging
from .db import session_factory
from .email_service import deliver_pending
from .sla_service import process_escalations


def run_once():
    with session_factory()() as db:
        count = deliver_pending(db)
        process_escalations(db)
        db.commit()
        return count


if __name__ == "__main__":
    while True:
        try:
            run_once()
        except Exception:
            logging.error('{"event":"email.worker_unavailable"}')
        time.sleep(5)
