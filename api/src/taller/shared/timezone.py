"""Shared Honduran time-zone helpers (AD-7).

`taller.workorders.application.use_cases` keeps its own `HONDURAS_TZ`
constant for the daily cash summary; adopting this shared module there
is a follow-up, out of scope for this change. Every new invoicing use
case that needs "today" in Honduras reads it from here instead, so the
fecha límite comparison and the cash summary's day boundary share one
time zone definition even though they are not yet the same code path.
"""

from datetime import date
from zoneinfo import ZoneInfo

from taller.identity.application.ports import Clock

HONDURAS_TZ = ZoneInfo("America/Tegucigalpa")


def local_today(clock: Clock) -> date:
    """Today's calendar date in `America/Tegucigalpa`, read through the
    injectable clock so tests can move time (AD-7).
    """
    return clock.now().astimezone(HONDURAS_TZ).date()
