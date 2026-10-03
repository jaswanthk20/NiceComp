import json
import logging


def event(name: str, **fields):
    """Operational IDs/counts only. Never log text, addresses, tokens or credentials."""
    logging.getLogger("nicecomp").info(json.dumps({"event": name, **fields}, default=str))
