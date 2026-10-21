"""Delivery on the simulation clock. An order given at minute s first acts over (s, s + 1]."""
from __future__ import annotations

from ..state import CoreInvariantError


def check_window(start_minute, stop_minute) -> None:
    if isinstance(start_minute, bool) or not isinstance(start_minute, int) or start_minute < 0:
        raise CoreInvariantError("an intervention starts at a whole minute >= 0")
    if stop_minute is not None and (isinstance(stop_minute, bool) or not isinstance(stop_minute, int)
                                    or stop_minute < start_minute):
        raise CoreInvariantError("an intervention stops at or after its start")


def delivered_by(minute: int, *, amount: float, start_minute: int, duration_min: float | None,
                 untimed_rate_per_min: float, stop_minute: int | None) -> float:
    """Cumulative amount delivered by the end of ``minute``.

    A timed order runs evenly over its duration; an untimed one at the default rate
    until the amount is in. A stopped order keeps what it had delivered when stopped.
    """
    if stop_minute is not None:
        minute = min(minute, stop_minute)
    elapsed = minute - start_minute
    if elapsed <= 0:
        return 0.0
    if duration_min is not None:
        return amount * min(1, max(0, elapsed / duration_min))
    return min(amount, untimed_rate_per_min * elapsed)


def given_in(minute: int, **delivery) -> float:
    """Amount delivered during the interval (minute - 1, minute]."""
    return delivered_by(minute, **delivery) - delivered_by(minute - 1, **delivery)
