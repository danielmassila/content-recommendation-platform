from io import StringIO

import pytest

from reco_ml.movielens_csv import iter_ratings


def test_source_time_and_identical_duplicates():
    rows = list(iter_ratings(StringIO('userId,movieId,rating,timestamp\n42,2571,0.5,1000000000\n42,2571,0.5,1000000000\n')))
    assert [line for line, _ in rows] == [2, 3]
    assert rows[0][1].rated_at.timestamp() == 1000000000
    assert rows[0][1].rated_at.utcoffset().total_seconds() == 0


@pytest.mark.parametrize('row', ['0,2571,4,1', '42,0,4,1', '42,2571,4.49,1', '42,2571,NaN,1', '42,2571,5.5,1', '42,2571,4,-1', '42,2571,4', '42,2571,4,1,extra'])
def test_invalid_rating_fails(row):
    with pytest.raises(ValueError):
        list(iter_ratings(StringIO('userId,movieId,rating,timestamp\n' + row)))



def test_reader_keeps_conflicting_rows_for_publication_validation():
    rows = list(iter_ratings(StringIO(
        'userId,movieId,rating,timestamp\n42,2571,4,1\n42,2571,5,1\n'
    )))
    assert [rating.rating for _, rating in rows] == [4, 5]


def test_reader_is_lazy_and_reports_invalid_source_line():
    rows = iter_ratings(StringIO(
        'userId,movieId,rating,timestamp\n42,2571,4,1\n42,2571,invalid,1\n'
    ))
    assert next(rows)[0] == 2
    with pytest.raises(ValueError, match='line 3'):
        next(rows)
