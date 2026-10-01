import io
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from reco_ml.catalog_sync import sync_catalog
from reco_ml.movie_mapping import MappingConflict


def source(rows='1,0114709,862\n2,0113497,8844\n'):
    return io.StringIO('movieId,imdbId,tmdbId\n' + rows)


def connection(rows=None):
    conn = MagicMock(autocommit=True)
    conn.execute.return_value.fetchall.return_value = rows or []
    return conn


@patch('reco_ml.catalog_sync.upsert_tmdb_movie')
def test_limits_requests_and_commits_movies_separately(upsert):
    conn, client = connection(), MagicMock()
    client.get_movie.return_value = {'id': 862, 'imdb_id': 'tt0114709'}
    report = sync_catalog(conn, source(), client, limit=1, delay=0)
    assert report['synced'] == 1
    assert report['deferred'] == 1
    client.get_movie.assert_called_once_with(862)
    upsert.assert_called_once_with(conn, client.get_movie.return_value)
    assert conn.transaction.return_value.__exit__.call_args_list[1].args == (None, None, None)


def test_existing_movies_do_not_use_request_budget():
    conn, client = connection([(862, None, 'tt0114709')]), MagicMock()
    report = sync_catalog(conn, source('1,0114709,862\n'), client, limit=1)
    assert report['existing'] == 1
    assert report['attempted'] == 0
    client.get_movie.assert_not_called()


@patch('reco_ml.catalog_sync.upsert_tmdb_movie')
def test_404_continues_to_next_movie(upsert):
    client = MagicMock()
    client.get_movie.side_effect = [HTTPError('url', 404, 'missing', {}, None), {'id': 8844}]
    report = sync_catalog(connection(), source(), client, delay=0)
    assert report['not_found'] == [862]
    assert report['synced'] == 1
    upsert.assert_called_once()


@patch('reco_ml.catalog_sync.upsert_tmdb_movie')
def test_outage_stops_after_preserving_previous_movie(upsert):
    conn, client = connection(), MagicMock()
    client.get_movie.side_effect = [{'id': 862}, HTTPError('url', 503, 'outage', {}, None)]
    with pytest.raises(HTTPError):
        sync_catalog(conn, source(), client, delay=0)
    upsert.assert_called_once()
    assert conn.transaction.return_value.__exit__.call_args_list[1].args == (None, None, None)


@pytest.mark.parametrize('rows', [[(999, 1, None)], [(862, 2, None)], [(862, None, 'tt9999999')]])
def test_existing_identity_conflicts_stop_before_http(rows):
    client = MagicMock()
    with pytest.raises(MappingConflict):
        sync_catalog(connection(rows), source(), client)
    client.get_movie.assert_not_called()


@patch('reco_ml.catalog_sync.upsert_tmdb_movie')
def test_api_imdb_conflict_never_writes(upsert):
    client = MagicMock()
    client.get_movie.return_value = {'id': 862, 'imdb_id': 'tt9999999'}
    with pytest.raises(MappingConflict):
        sync_catalog(connection(), source(), client)
    upsert.assert_not_called()


def test_missing_and_ambiguous_links_are_reported_without_http():
    client = MagicMock()
    report = sync_catalog(connection(), source('1,,862\n2,,862\n3,,\n'), client)
    assert report['missing_tmdb_id'] == [3]
    assert report['rejected_links'] == {1: 'ambiguous_link', 2: 'ambiguous_link'}
    client.get_movie.assert_not_called()


@pytest.mark.parametrize('options', [{'limit': 0}, {'delay': -1}, {'delay': float('nan')}])
def test_invalid_options(options):
    with pytest.raises(ValueError):
        sync_catalog(connection(), source(), MagicMock(), **options)
