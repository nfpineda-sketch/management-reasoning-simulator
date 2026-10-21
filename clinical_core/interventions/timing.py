"""Delivery on the simulation clock. An order given at minute s first acts over (s, s + 1].

A timed order runs evenly over its duration from its start, which may be fractional when
the order was queued behind an earlier bag of the same kind (the family engine starts a
second bag when the first is due to finish). An untimed order runs at the default rate,
behind whatever untimed volume of the same kind was still queued when it was given: the
default rate is one shared line, not one per order.
"""
from __future__ import annotations

import math

from ..state import CoreInvariantError


def _number(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value)


def check_window(start_minute, stop_minute, *, whole_start: bool = False) -> None:
    if not _number(start_minute) or start_minute < 0 or (whole_start and not isinstance(start_minute, int)):
        raise CoreInvariantError("an intervention starts at a minute >= 0")
    if stop_minute is not None and (isinstance(stop_minute, bool) or not isinstance(stop_minute, int)
                                    or stop_minute < 0):
        raise CoreInvariantError("an intervention stops at a whole minute >= 0")


def check_queue(value) -> None:
    if not _number(value) or value < 0:
        raise CoreInvariantError("the amount queued ahead of an order is a non-negative number")


def delivered_by(minute: int, *, amount: float, start_minute: float, duration_min: float | None,
                 untimed_rate_per_min: float, stop_minute: int | None, queued_ahead: float = 0.0) -> float:
    """Cumulative amount delivered by the end of ``minute``. A stopped order keeps what it had delivered."""
    if stop_minute is not None:
        minute = min(minute, stop_minute)
    elapsed = minute - start_minute
    if elapsed <= 0:
        return 0.0
    if duration_min is not None:
        return amount * min(1, max(0, elapsed / duration_min))
    return min(amount, max(0.0, untimed_rate_per_min * elapsed - queued_ahead))


def given_in(minute: int, **delivery) -> float:
    """Amount delivered during the interval (minute - 1, minute]."""
    return delivered_by(minute, **delivery) - delivered_by(minute - 1, **delivery)
