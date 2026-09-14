"""Cancellation applies exclusively to unexecuted encounter orders."""
import re
from shared_order_language import _normalize


def is_cancellation(text):
    return bool(re.fullmatch(r"(?:cancel|cancelar|cancela|discard|descartar)(?: (?:the |la |las )?(?:pending orders?|orders?|orden(?:es)?(?: pendientes?)?|indicaciones(?: pendientes?)?))?[.!]?", _normalize(text).strip()))


def clear_pending_orders(session):
    keys = ("pending_reasoning", "pending_action", "pending_bundle")
    if not any(session.get(k) for k in keys):
        return False
    for key in keys:
        session[key] = None
    return True
