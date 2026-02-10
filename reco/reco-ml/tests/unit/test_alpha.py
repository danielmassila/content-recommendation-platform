import pytest
from reco_ml.algo import (
    compute_profile_maturity_threshold,
    compute_alpha,
    mix_scores,
    top_n,
)


def test_profile_maturity_threshold_median():
    ratings = [
        (1, 10, 4.0),
        (1, 11, 3.0),
        (1, 12, 5.0),  # 3 ratings
        (2, 10, 4.0),  # 1 rating
        (3, 10, 2.0),
        (3, 11, 2.0),  # 2 ratings
    ]
    # counts = [3,1,2] median = 2
    assert compute_profile_maturity_threshold(ratings) == 2


def test_profile_maturity_threshold_raises_if_empty():
    with pytest.raises(ValueError):
        compute_profile_maturity_threshold([])


def test_compute_alpha_bounds_and_cap():
    assert compute_alpha(0, 10) == 0.0
    assert 0.0 <= compute_alpha(5, 10) <= 1.0
    assert compute_alpha(10_000, 1, alpha_max=0.9) == 0.9


def test_mix_scores_union_of_items():
    cf = {1: 1.0, 2: 0.0}
    pop = {2: 1.0, 3: 0.5}
    mixed = mix_scores(cf, pop, alpha=0.5)
    assert set(mixed.keys()) == {1, 2, 3}
    assert mixed[1] == 0.5  # pop missing => 0
    assert mixed[2] == 0.5
    assert mixed[3] == 0.25  # cf missing => 0


def test_top_n_edge_cases():
    assert top_n({}, 10) == []
    assert top_n({1: 0.2}, 0) == []
    assert top_n({1: 0.2, 2: 0.9}, 1) == [(2, 0.9)]
