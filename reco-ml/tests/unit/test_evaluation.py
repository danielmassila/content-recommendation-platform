"""Check the extracted evaluation helpers on a small, known ranking."""

import pytest

from reco_ml.evaluation import precision_recall_ap_at_k, split_ratings_by_user


def test_ranking_metrics_for_two_relevant_items():
    precision, recall, average_precision = precision_recall_ap_at_k(
        [10, 20, 30], {10, 30}, 3
    )
    assert precision == pytest.approx(2 / 3)
    assert recall == 1
    assert average_precision == pytest.approx((1 + 2 / 3) / 2)


def test_split_is_reproducible_and_keeps_test_ratings_out_of_training():
    ratings = [(user, item, 4.0) for user in (1, 2) for item in range(5)]
    train, test = split_ratings_by_user(ratings, 'loo', 0.2, 42)
    assert (train, test) == split_ratings_by_user(ratings, 'loo', 0.2, 42)
    assert len(test) == 2
    assert not set(train).intersection(test)
    assert sorted(train + test) == sorted(ratings)
