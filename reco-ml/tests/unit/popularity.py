import pytest
from reco_ml.algo import (
    choose_m,
    normalize_scores,
    compute_popularity_from_stats,
    top_n,
)


def test_choose_valid_m():
    counts = [1, 2, 3, 4, 10]
    # quantile 0.80 => ceil(0.8*5)-1 = ceil(4)-1 = 3 => 4
    assert choose_m(counts, 0.80) == 4.0


def test_choose_m_empty_raises():
    with pytest.raises(ValueError):
        choose_m([], 0.80)


def test_choose_invalid_m_quantile_raises():
    with pytest.raises(ValueError):
        choose_m([1, 2, 3], 1.0)
    with pytest.raises(ValueError):
        choose_m([1, 2, 3], 0.0)
    with pytest.raises(ValueError):
        choose_m([1, 2, 3], -0.1)


def test_normalize_scores_empty():
    assert normalize_scores({}) == {}


def test_normalize_scores_all_equal():
    assert normalize_scores({1: 5.0, 2: 5.0}) == {1: 0.0, 2: 0.0}


def test_normalize_scores_range():
    out = normalize_scores({1: 1.0, 2: 3.0, 3: 2.0})
    assert out[1] == 0.0
    assert out[2] == 1.0
    assert out[3] == 0.5


def test_compute_popularity_from_stats_empty():
    assert compute_popularity_from_stats({}, global_rating=3.0) == {}


def test_compute_popularity_from_stats_invalid_q():
    with pytest.raises(ValueError):
        compute_popularity_from_stats({1: (10, 4.0)}, global_rating=3.0, q=1.0)


def test_compute_popularity_from_stats_given_m_and_normalized():
    stats_by_items = {
        1: (10, 4.0),
        2: (1, 5.0),
        3: (50, 3.0),
    }
    scores = compute_popularity_from_stats(stats_by_items, global_rating=3.5, m=10.0)
    assert set(scores.keys()) == {1, 2, 3}
    assert min(scores.values()) == pytest.approx(0.0)
    assert max(scores.values()) == pytest.approx(1.0)


def test_top_n_descending():
    scores = {1: 0.2, 2: 0.9, 3: 0.5}
    ranked = top_n(scores, n=10)
    assert ranked == [(2, 0.9), (3, 0.5), (1, 0.2)]
