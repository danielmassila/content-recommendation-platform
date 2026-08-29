import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

from jobs.enrich_tmdb import _merge_metadata, _request_tmdb_movie


def test_merge_metadata_preserves_source_ids_and_tracks_enrichment_time():
    merged = _merge_metadata(
        {"movieLensId": 1, "tmdbId": 42},
        {"id": 42, "title": "Example", "genres": [], "credits": {}},
    )

    assert merged["movieLensId"] == 1
    assert merged["tmdb"]["id"] == 42
    assert merged["source"] == "movielens+tmdb"
    assert merged["tmdbEnrichedAt"].endswith("+00:00")


def test_tmdb_request_retries_transient_http_errors():
    transient_error = urllib.error.HTTPError(
        "https://example.test",
        503,
        "Unavailable",
        {},
        io.BytesIO(),
    )
    response = MagicMock()
    response.__enter__.return_value.read.return_value = json.dumps({"id": 42}).encode()

    with patch("jobs.enrich_tmdb.urllib.request.urlopen", side_effect=[transient_error, response]) as urlopen:
        with patch("jobs.enrich_tmdb.time.sleep") as sleep:
            payload = _request_tmdb_movie(42, "secret")

    assert payload == {"id": 42}
    assert urlopen.call_count == 2
    sleep.assert_called_once_with(1)


def test_tmdb_request_does_not_retry_not_found():
    not_found = urllib.error.HTTPError(
        "https://example.test",
        404,
        "Not found",
        {},
        io.BytesIO(),
    )

    with patch("jobs.enrich_tmdb.urllib.request.urlopen", side_effect=not_found) as urlopen:
        try:
            _request_tmdb_movie(999, "secret")
        except urllib.error.HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("Expected HTTPError")

    assert urlopen.call_count == 1
