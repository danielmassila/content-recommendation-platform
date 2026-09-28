from jobs.enrich_tmdb import _merge_metadata
from unittest.mock import MagicMock, patch

from jobs.enrich_tmdb import main


def test_merge_metadata_preserves_source_ids_and_tracks_enrichment_time():
    merged = _merge_metadata(
        {"movieLensId": 1, "tmdbId": 42},
        {"id": 42, "title": "Example", "genres": [], "credits": {}},
    )

    assert merged["movieLensId"] == 1
    assert merged["tmdb"]["id"] == 42
    assert merged["source"] == "movielens+tmdb"
    assert merged["tmdbEnrichedAt"].endswith("+00:00")


def test_enrichment_uses_shared_client_and_preserves_internal_item_id(monkeypatch):
    monkeypatch.setenv("TMDB_API_KEY", "test-key")
    monkeypatch.setenv("TMDB_REQUEST_DELAY_SECONDS", "0")
    connection = MagicMock()
    with patch("jobs.enrich_tmdb.TmdbClient") as client_class, \
            patch("jobs.enrich_tmdb.get_db_connection") as connect, \
            patch("jobs.enrich_tmdb._fetch_items_to_enrich", return_value=[(125, {"tmdbId": 603})]), \
            patch("jobs.enrich_tmdb._update_item_metadata") as update:
        connect.return_value.__enter__.return_value = connection
        client_class.return_value.get_movie.return_value = {"id": 603, "genres": [], "credits": {}}
        main()
    client_class.assert_called_once_with("test-key")
    client_class.return_value.get_movie.assert_called_once_with(603)
    assert update.call_args.args[0] is connection
    assert update.call_args.args[1] == 125
    assert update.call_args.args[2]["tmdb"]["id"] == 603
    connection.commit.assert_called()
