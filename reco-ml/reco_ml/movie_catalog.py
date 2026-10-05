"""Persist TMDB films without importing users or resetting application data."""

import re
from datetime import datetime, timezone

from psycopg import Connection
from psycopg.types.json import Jsonb

from reco_ml.movie_mapping import MappingConflict
from reco_ml.tmdb_metadata import to_tmdb_metadata


def upsert_tmdb_movie(conn, payload: dict) -> int:
    """Return the internal item ID. The caller owns the transaction/commit.

    Legacy JSON-only identities require an audited backfill before ingestion.
    Missing IMDb IDs do not erase existing IDs. A contradictory IMDb ID blocks
    the update. TMDB metadata replaces provider fields, preserving other keys.
    """
    tmdb_id = payload.get("id")
    title = payload.get("title")
    imdb_id = payload.get("imdb_id") or None
    if type(tmdb_id) is not int or tmdb_id <= 0:
        raise ValueError("A positive TMDB ID is required")
    if not isinstance(title, str) or not title.strip() or len(title) > 255:
        raise ValueError("A non-empty title of at most 255 characters is required")
    if imdb_id is not None and (not isinstance(imdb_id, str) or len(imdb_id) > 32
                                or not re.fullmatch(r"tt[0-9]+", imdb_id)):
        raise ValueError("Invalid IMDb ID")
    synced_at = datetime.now(timezone.utc)
    metadata = to_tmdb_metadata(payload)
    metadata = {key: value for key, value in metadata.items() if value is not None}
    metadata.update(tmdbId=tmdb_id, tmdbEnrichedAt=synced_at.isoformat())
    if imdb_id:
        metadata["imdbId"] = imdb_id
    with conn.cursor() as cur:
        # Do not create a second film next to an unmigrated legacy row.
        cur.execute("""
            SELECT id FROM items WHERE type = 'MOVIE'
              AND (metadata->>'tmdbId' = %s OR metadata->'tmdb'->>'id' = %s)
              AND (tmdb_id IS NULL OR tmdb_id <> %s)
            LIMIT 1
            """, (str(tmdb_id), str(tmdb_id), tmdb_id))
        if cur.fetchone():
            raise MappingConflict("Legacy TMDB identity requires an audited backfill")
        cur.execute("""
            INSERT INTO items (title, type, tmdb_id, imdb_id, metadata, tmdb_last_synced_at)
            VALUES (%s, 'MOVIE', %s, %s, %s || '{"source":"tmdb"}'::jsonb, %s)
            ON CONFLICT (tmdb_id) WHERE type = 'MOVIE'
            DO UPDATE SET
                title = EXCLUDED.title,
                imdb_id = COALESCE(EXCLUDED.imdb_id, items.imdb_id),
                tmdb_last_synced_at = EXCLUDED.tmdb_last_synced_at,
                metadata = COALESCE(items.metadata, '{}'::jsonb)
                    || (EXCLUDED.metadata - 'source')
                    || jsonb_build_object('source', CASE
                        WHEN items.movielens_id IS NOT NULL
                          OR items.metadata ? 'movieLensId' THEN 'movielens+tmdb'
                        ELSE 'tmdb' END)
            WHERE items.imdb_id IS NULL OR EXCLUDED.imdb_id IS NULL
                OR items.imdb_id = EXCLUDED.imdb_id
            RETURNING id
            """, (title.strip(), tmdb_id, imdb_id, Jsonb(metadata), synced_at))
        row = cur.fetchone()
        if row is None:
            raise MappingConflict("Catalog and TMDB disagree on IMDb identity")
        return row[0]


def find_movie_identities(
    conn: Connection, *, tmdb_id: int | None, movielens_id: int
) -> list[tuple[int | None, int | None, str | None]]:
    """Read all matching identities; the caller decides whether they agree.

    Match either source ID so conflicting mappings remain visible. This helper
    neither commits nor selects a preferred row when several movies match.
    """
    return conn.execute(
        """
        SELECT tmdb_id, movielens_id, imdb_id
        FROM items
        WHERE type = 'MOVIE' AND (tmdb_id = %s OR movielens_id = %s)
        """,
        (tmdb_id, movielens_id),
    ).fetchall()


def fetch_catalog_movies(conn):
    """Read explicit movie identities used to resolve MovieLens links."""
    from reco_ml.movie_mapping import CatalogMovie

    return [CatalogMovie(*row) for row in conn.execute(
        "SELECT id,tmdb_id,movielens_id,imdb_id FROM items WHERE type='MOVIE' AND tmdb_id IS NOT NULL"
    )]
