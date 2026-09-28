import io
import json
import urllib.error
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from reco_ml.tmdb_client import TmdbClient, _retry_delay


def response(payload):
    result = MagicMock()
    result.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return result


def http_error(code, headers=None):
    return urllib.error.HTTPError("https://example.test", code, "Failure", headers or {}, io.BytesIO())


def test_fetches_details_and_credits_with_configured_timeout():
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", return_value=response({"id": 603})) as fetch:
        assert TmdbClient("test-key", timeout=7).get_movie(603) == {"id": 603}
    request = fetch.call_args.args[0]
    url = urlparse(request.full_url)
    assert url.path == "/3/movie/603"
    assert parse_qs(url.query) == {"api_key": ["test-key"], "language": ["fr-FR"], "append_to_response": ["credits"]}
    assert fetch.call_args.kwargs == {"timeout": 7}


@pytest.mark.parametrize("code", [400, 401, 403, 404])
def test_permanent_http_errors_propagate_without_retry(code):
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", side_effect=http_error(code)) as fetch, \
            patch("reco_ml.tmdb_client.time.sleep") as sleep:
        with pytest.raises(urllib.error.HTTPError) as caught:
            TmdbClient("key").get_movie(603)
    assert caught.value.code == code
    assert fetch.call_count == 1
    sleep.assert_not_called()


@pytest.mark.parametrize("error,delay", [
    (http_error(503), 1),
    (http_error(429, {"Retry-After": "7"}), 7),
    (http_error(429, {"Retry-After": "invalid"}), 1),
    (urllib.error.URLError("connection lost"), 1),
    (TimeoutError(), 1),
])
def test_transient_failure_recovers(error, delay):
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", side_effect=[error, response({"id": 603})]) as fetch, \
            patch("reco_ml.tmdb_client.time.sleep") as sleep:
        assert TmdbClient("key").get_movie(603)["id"] == 603
    assert fetch.call_count == 2
    sleep.assert_called_once_with(delay)


def test_retry_budget_is_bounded():
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", side_effect=TimeoutError()) as fetch, \
            patch("reco_ml.tmdb_client.time.sleep") as sleep:
        with pytest.raises(TimeoutError):
            TmdbClient("key").get_movie(603)
    assert fetch.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]


@pytest.mark.parametrize("payload", [[], {}, {"id": 604}, {"id": "603"}])
def test_invalid_payload_is_not_retried(payload):
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", return_value=response(payload)) as fetch:
        with pytest.raises(ValueError):
            TmdbClient("key").get_movie(603)
    assert fetch.call_count == 1


def test_invalid_json_is_not_retried():
    invalid = response(None)
    invalid.__enter__.return_value.read.return_value = b"not json"
    with patch("reco_ml.tmdb_client.urllib.request.urlopen", return_value=invalid) as fetch:
        with pytest.raises(ValueError):
            TmdbClient("key").get_movie(603)
    assert fetch.call_count == 1


@pytest.mark.parametrize("tmdb_id", [0, -1, True, "603", 603.5])
def test_invalid_id_never_calls_api(tmdb_id):
    with patch("reco_ml.tmdb_client.urllib.request.urlopen") as fetch:
        with pytest.raises(ValueError):
            TmdbClient("key").get_movie(tmdb_id)
    fetch.assert_not_called()


def test_retry_after_date_and_nonfinite_values():
    future = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=60))
    assert 58 <= _retry_delay(future, 0) <= 60
    assert _retry_delay("NaN", 2) == 4
    assert _retry_delay("-1", 0) == 0


@pytest.mark.parametrize("kwargs", [{"api_key": ""}, {"api_key": "key", "timeout": 0},
                                    {"api_key": "key", "max_attempts": 0}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        TmdbClient(**kwargs)
