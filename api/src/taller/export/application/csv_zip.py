"""Pure CSV and ZIP building helpers for the workshop data export.

No framework or database import: every function here takes already-fetched
Python values and returns bytes, so it is unit-testable with no database
(`design.md`'s AD-13, and the "Export" section's formatting rules).
"""

import csv
import io
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

#: Every exported timestamp is rendered in the workshop's local time, the
#: same zone the daily cash summary uses for its day boundary (AD-20).
HONDURAS_TZ = ZoneInfo("America/Tegucigalpa")

#: A text cell starting with one of these is read by Excel/Sheets as a
#: formula, not literal text -- the classic CSV formula-injection vector.
_RISKY_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

#: A cell as produced by `taller/export/adapters/sources.py`. `str` is the
#: only type the formula-injection guard ever inspects; every other type
#: (a count, a lempira amount) is a "numeric column" the guard never touches,
#: per `design.md`'s "Formula-injection guard" rule.
CellValue = str | int | Decimal | bool | None


def format_money(cents: int | None) -> Decimal | None:
    """Render integer cents as lempiras with a `.` decimal separator.

    Returns a `Decimal`, never a `str`: the formula-injection guard only
    ever inspects `str` cells, so a negative balance (e.g. "a saldo a
    favor") is written as `-50.00` and never escaped, matching "numeric
    columns are never prefixed".
    """
    if cents is None:
        return None
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_local_timestamp(value: datetime | None) -> str:
    """Render a UTC-aware timestamp as Honduran local time, `YYYY-MM-DD HH:MM:SS`."""
    if value is None:
        return ""
    return value.astimezone(HONDURAS_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _guard_formula_injection(value: str) -> str:
    if value.startswith(_RISKY_PREFIXES):
        return f"'{value}"
    return value


def _render_cell(value: CellValue) -> object:
    if value is None:
        return ""
    if isinstance(value, str):
        return _guard_formula_injection(value)
    return value


def build_csv(headers: Sequence[str], rows: Iterable[Sequence[CellValue]]) -> bytes:
    """Write one CSV, encoded `utf-8-sig` (BOM), header row first.

    No `sep=,` line: it would make Excel ignore the BOM and garble accented
    characters (`design.md`'s "Export" section).
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(_render_cell(cell) for cell in row)
    return buffer.getvalue().encode("utf-8-sig")


def build_zip(files: Mapping[str, bytes]) -> bytes:
    """Collect several named CSVs into one in-memory ZIP (deflate)."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)
    return buffer.getvalue()
