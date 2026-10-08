"""schema qualify unaccent lower for pg_dump restore

Revision ID: 1a57ba6a8108
Revises: db3dfe52854a
Create Date: 2026-10-08 00:58:17.715464

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a57ba6a8108"
down_revision: str | Sequence[str] | None = "db3dfe52854a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_UNACCENT_LOWER_FUNCTION = "taller_unaccent_lower"

#: pg_dump's plain-text/custom output runs under
#: `SELECT pg_catalog.set_config('search_path', '', false)` (deliberately
#: empty, so a restore can never be hijacked by an attacker-controlled
#: search_path). `taller_unaccent_lower`'s original body -- added in
#: 3571335f9414_create_inventory_items_and_movements_.py -- was
#: `RETURN lower(unaccent('unaccent'::regdictionary, $1));`, which resolves
#: both the two-argument `unaccent()` function and the `unaccent` text
#: search dictionary named in the regdictionary cast through search_path.
#: CREATE FUNCTION itself only stores that text, so a restore recreates the
#: function fine; it is CREATE UNIQUE INDEX ix_inventory_items_active_name
#: (which must evaluate the function to validate the index) that runs next,
#: under the restore's empty search_path, and fails with "text search
#: dictionary unaccent does not exist" -- the dump never completes, and the
#: index is missing from the restored database.
#:
#: The fix schema-qualifies both references so the function resolves
#: correctly under any search_path, including empty. It never assumes the
#: extension lives in "public": some environments install extensions into a
#: dedicated schema, so the actual schema is looked up from pg_extension at
#: migration time and safely quoted with quote_ident()/format('%I', ...)
#: rather than concatenated as a raw string.
_PREVIOUS_FUNCTION_BODY = "RETURN lower(unaccent('unaccent'::regdictionary, $1));"


def upgrade() -> None:
    """Upgrade schema."""
    # Still LANGUAGE plpgsql, not sql, for the same reason the original
    # migration gives: a single-statement SQL function is eligible for
    # inline expansion, which would re-introduce the exact search_path
    # resolution problem this migration fixes.
    op.execute(
        f"""
        DO $outer$
        DECLARE
            unaccent_schema text;
            qualified_dictionary text;
        BEGIN
            SELECT n.nspname INTO unaccent_schema
            FROM pg_catalog.pg_extension e
            JOIN pg_catalog.pg_namespace n ON n.oid = e.extnamespace
            WHERE e.extname = 'unaccent';

            IF unaccent_schema IS NULL THEN
                RAISE EXCEPTION 'the unaccent extension is not installed';
            END IF;

            -- quote_ident() rather than string concatenation: the schema
            -- name is safely embedded as an identifier even if it needs
            -- quoting (reserved word, mixed case, special characters).
            qualified_dictionary := quote_ident(unaccent_schema) || '.unaccent';

            EXECUTE format(
                'CREATE OR REPLACE FUNCTION {_UNACCENT_LOWER_FUNCTION}(text) '
                'RETURNS text AS $body$ '
                'BEGIN '
                'RETURN lower(%I.unaccent((%L)::regdictionary, $1)); '
                'END; '
                '$body$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE STRICT',
                unaccent_schema,
                qualified_dictionary
            );
        END
        $outer$
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        f"CREATE OR REPLACE FUNCTION {_UNACCENT_LOWER_FUNCTION}(text) RETURNS text AS $$ "
        "BEGIN "
        f"{_PREVIOUS_FUNCTION_BODY} "
        "END; "
        "$$ LANGUAGE plpgsql IMMUTABLE PARALLEL SAFE STRICT"
    )
