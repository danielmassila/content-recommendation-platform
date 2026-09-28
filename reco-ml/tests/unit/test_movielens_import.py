from io import StringIO

import pytest

from reco_ml.movielens_import import parse_ratings, read_snapshot


def test_source_time_and_identical_duplicates():
    rows = parse_ratings(StringIO('userId,movieId,rating,timestamp\n42,2571,0.5,1000000000\n42,2571,0.5,1000000000\n'))
    assert len(rows) == 1
    assert rows[0].rated_at.timestamp() == 1000000000
    assert rows[0].rated_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize('row', ['0,2571,4,1', '42,0,4,1', '42,2571,4.49,1', '42,2571,NaN,1', '42,2571,5.5,1', '42,2571,4,-1', '42,2571,4', '42,2571,4,1,extra'])
def test_invalid_rating_fails(row):
    with pytest.raises(ValueError):
        parse_ratings(StringIO('userId,movieId,rating,timestamp\n' + row))


def test_contradictory_duplicate_fails():
    with pytest.raises(ValueError):
        parse_ratings(StringIO('userId,movieId,rating,timestamp\n42,2571,4,1\n42,2571,5,1\n'))


def test_snapshot_identity_changes_with_source_bytes(tmp_path):
    (tmp_path / 'links.csv').write_text('movieId,imdbId,tmdbId\n2571,0133093,603\n')
    ratings = tmp_path / 'ratings.csv'
    ratings.write_text('userId,movieId,rating,timestamp\n42,2571,4,1\n')
    first = read_snapshot(tmp_path)[0]
    assert read_snapshot(tmp_path)[0] == first
    ratings.write_text('userId,movieId,rating,timestamp\n42,2571,5,1\n')
    assert read_snapshot(tmp_path)[0] != first
