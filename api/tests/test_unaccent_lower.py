"""Covers the pg_dump restore fix for `taller_unaccent_lower`.

A `pg_dump` restore runs under `SELECT pg_catalog.set_config('search_path',
'', false)`, deliberately empty so a restore can never be hijacked by an
attacker-controlled search_path. Before the schema-qualifying migration
(1a57ba6a8108), the function's body resolved both the two-argument
`unaccent()` function and the `unaccent` text search dictionary through
search_path, so evaluating it under an empty search_path -- exactly what
CREATE UNIQUE INDEX ix_inventory_items_active_name does during a restore --
fails with "text search dictionary unaccent does not exist".
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


def test_taller_unaccent_lower_resolves_under_an_empty_search_path(db_session: Session) -> None:
    """The function must fold case and strip accents without relying on
    search_path to find `unaccent` or the `unaccent` text search
    dictionary, so a `pg_dump` restore (which runs under an empty
    search_path) can evaluate it while validating the functional index.
    """
    db_session.execute(text("SET LOCAL search_path TO ''"))

    result = db_session.execute(
        text("SELECT public.taller_unaccent_lower('Ñandú ÁRBOL')")
    ).scalar_one()

    assert result == "nandu arbol"
