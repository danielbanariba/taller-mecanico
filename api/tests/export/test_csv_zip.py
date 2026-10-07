"""Tests for the pure CSV/ZIP builder (`design.md`'s AD-13 and its "Export"
formatting rules). No database: every input is built in memory.

Defects these catch:
- a missing UTF-8 BOM, which makes Excel on Windows mojibake accented names;
- an encoding step that silently strips or mangles accented characters;
- formula injection in Excel/Sheets through an unescaped text cell;
- numeric columns wrongly escaped by the same guard, corrupting a negative
  balance or delta;
- a missing file instead of a header-only CSV for an entity with no rows.
"""

import csv
import io

from taller.export.application.csv_zip import build_csv


def _parse(csv_bytes: bytes) -> list[list[str]]:
    text = csv_bytes.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


def test_every_csv_starts_with_the_utf8_bom() -> None:
    csv_bytes = build_csv(["id"], [["1"]])

    assert csv_bytes[:3] == b"\xef\xbb\xbf"


def test_accented_content_round_trips_byte_for_byte() -> None:
    csv_bytes = build_csv(["full_name"], [["José Núñez"]])

    rows = _parse(csv_bytes)

    assert rows == [["full_name"], ["José Núñez"]]


def test_a_text_cell_starting_with_a_formula_character_is_escaped() -> None:
    csv_bytes = build_csv(["note"], [["=1+1"]])

    rows = _parse(csv_bytes)

    assert rows[1] == ["'=1+1"]


def test_a_negative_numeric_cell_is_not_escaped() -> None:
    csv_bytes = build_csv(["delta"], [[-5]])

    rows = _parse(csv_bytes)

    assert rows[1] == ["-5"]


def test_an_empty_table_still_produces_a_header_only_csv() -> None:
    csv_bytes = build_csv(["id", "name"], [])

    rows = _parse(csv_bytes)

    assert rows == [["id", "name"]]
