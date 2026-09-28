"""Run only against an explicitly supplied disposable PostgreSQL database."""

import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest

from reco_ml.movie_catalog import upsert_tmdb_movie
from reco_ml.movie_mapping import MappingConflict

DSN = os.getenv("CATALOG_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="CATALOG_TEST_DSN must point to a disposable database")


@pytest.fixture(scope="module", autouse=True)
def schema():
    if not DSN:
        return
    migrations = Path(__file__).resolve().parents[3] / "backend/src/main/resources/db/migration"
    with psycopg.connect(DSN) as conn:
        for migration in sorted(migrations.glob("V*__*.sql")):
            conn.execute(migration.read_text())


def payload(tmdb_id):
    return {"id": tmdb_id, "title": "Example", "imdb_id": "tt0133093",
            "genres": [{"name": "Science Fiction"}], "poster_path": None}


def test_create_update_and_keep_application_references():
    with psycopg.connect(DSN) as conn:
        item_id = upsert_tmdb_movie(conn, payload(603))
        row = conn.execute("SELECT movielens_id, metadata, tmdb_last_synced_at FROM items WHERE id=%s", (item_id,)).fetchone()
        assert row[0] is None
        assert row[1]["source"] == "tmdb"
        assert row[1]["tmdb"]["posterPath"] is None
        assert row[2] is not None
        user_id = conn.execute("INSERT INTO users(email) VALUES ('app@example.com') RETURNING id").fetchone()[0]
        conn.execute("INSERT INTO ratings(user_id,item_id,rating) VALUES (%s,%s,4)", (user_id, item_id))
        conn.execute("UPDATE items SET movielens_id=2571, metadata=metadata || '{\"custom\":true}' WHERE id=%s", (item_id,))
        assert upsert_tmdb_movie(conn, {**payload(603), "title": "Updated", "imdb_id": None}) == item_id
        row = conn.execute("SELECT title, imdb_id, movielens_id, metadata FROM items WHERE id=%s", (item_id,)).fetchone()
        assert row[:3] == ("Updated", "tt0133093", 2571)
        assert row[3]["custom"] is True
        assert row[3]["source"] == "movielens+tmdb"
        assert conn.execute("SELECT item_id FROM ratings WHERE user_id=%s", (user_id,)).fetchone()[0] == item_id
        with pytest.raises(MappingConflict):
            upsert_tmdb_movie(conn, {**payload(603), "imdb_id": "tt9999999"})


def test_legacy_json_identity_blocks_duplicate_creation():
    with psycopg.connect(DSN) as conn:
        conn.execute("INSERT INTO items(title,type,metadata) VALUES ('Legacy','MOVIE','{\"tmdbId\":604}')")
        with pytest.raises(MappingConflict):
            upsert_tmdb_movie(conn, payload(604))
        assert conn.execute("SELECT count(*) FROM items WHERE tmdb_id=604").fetchone()[0] == 0


def test_concurrent_upserts_return_same_internal_id():
    def sync(_):
        with psycopg.connect(DSN) as conn:
            return upsert_tmdb_movie(conn, payload(605))
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(sync, range(2)))
    assert ids[0] == ids[1]
