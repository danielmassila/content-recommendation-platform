from unittest.mock import MagicMock

import pytest

from reco_ml.movie_catalog import upsert_tmdb_movie


@pytest.mark.parametrize("payload", [
    {"id": 0, "title": "Film"},
    {"id": True, "title": "Film"},
    {"id": 603, "title": " "},
    {"id": 603, "title": "x" * 256},
    {"id": 603, "title": "Film", "imdb_id": "0133093"},
])
def test_invalid_identity_or_title_never_touches_database(payload):
    conn = MagicMock()
    with pytest.raises(ValueError):
        upsert_tmdb_movie(conn, payload)
    conn.cursor.assert_not_called()
