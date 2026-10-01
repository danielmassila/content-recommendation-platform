from unittest.mock import MagicMock

import pytest

from reco_ml.rating_corpus import load_corpus
from reco_ml import algo


def test_identities_and_snapshot_are_explicit(monkeypatch):
    monkeypatch.setattr('reco_ml.rating_corpus.repositories.fetch_all_ratings', lambda conn: [(1, 10, 4.0)])
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = (True,)
    cursor.fetchall.return_value = [(1, 20, 5), (2, 10, 2)]
    ratings, stats, mean = load_corpus(conn, 'chosen-snapshot')
    assert ratings == [(1, 10, 4.0), (-1, 20, 5.0), (-2, 10, 2.0)]
    assert stats == {10: (2, 3.0), 20: (1, 5.0)}
    assert mean == 11 / 3
    assert cursor.execute.call_args.args[1] == ('chosen-snapshot',)


def test_unknown_snapshot_fails(monkeypatch):
    monkeypatch.setattr('reco_ml.rating_corpus.repositories.fetch_all_ratings', lambda conn: [])
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)
    with pytest.raises(ValueError, match='snapshot'):
        load_corpus(conn, 'unknown')


def test_external_neighbors_are_not_recommendation_recipients(monkeypatch):
    monkeypatch.setattr(algo.repositories, 'fetch_all_users', lambda conn: [1, 2])
    monkeypatch.setattr(algo.repositories, 'fetch_all_items', lambda conn: [10,20,30])
    monkeypatch.setattr(algo.repositories, 'fetch_all_item_profiles', lambda conn: {})
    monkeypatch.setattr(algo.repositories, 'fetch_user_preferences', lambda conn: {})
    monkeypatch.setattr(algo, 'load_corpus', lambda conn, version: (
        [(1,10,4.),(-1,10,5.),(-1,20,4.)], {10:(2,4.5),20:(1,4.)}, 4.33))
    captured=[]
    monkeypatch.setattr(algo.repositories, 'write_recommendations', lambda conn, rows: captured.extend(rows))
    algo.recompute_all_recommendations(object(), dataset_version='test')
    assert captured
    assert {row.user_id for row in captured} <= {1,2}
    assert all(row.item_id != 10 for row in captured if row.user_id == 1)


def test_unpublished_snapshot_is_rejected_before_reading_ratings(monkeypatch):
    read = MagicMock()
    monkeypatch.setattr('reco_ml.rating_corpus.repositories.fetch_all_ratings', read)
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (False,)
    with pytest.raises(ValueError, match='not published'):
        load_corpus(conn, 'incomplete')
    read.assert_not_called()
