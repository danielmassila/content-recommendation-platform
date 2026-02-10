import pytest
from reco_ml.algo import build_ratings_by_user, compute_user_cosine_similarity


def test_build_ratings_by_user():
    ratings = [(1, 10, 4.0), (1, 20, 2.0), (2, 10, 5.0)]
    ratings_by_user = build_ratings_by_user(ratings)
    assert ratings_by_user[1][10] == 4.0
    assert ratings_by_user[1][20] == 2.0
    assert ratings_by_user[2][10] == 5.0


def test_cosine_similarity_no_common_item_is_zero():
    by_user = {
        1: {10: 4.0},
        2: {20: 5.0},
    }
    assert compute_user_cosine_similarity(1, 2, by_user) == 0.0


def test_cosine_similarity_missing_user_is_zero():
    by_user = {1: {10: 4.0}}
    assert compute_user_cosine_similarity(1, 999, by_user) == 0.0


def test_cosine_similarity_with_common_item():
    by_user = {
        1: {10: 1.0, 20: 2.0},
        2: {10: 2.0, 20: 4.0},
    }
    assert compute_user_cosine_similarity(1, 2, by_user) == pytest.approx(
        1.0
    )  # v = ku so cos = 1


def test_cosine_similarity_common_zero_rates():
    by_user = {
        1: {10: 0.0},
        2: {10: 0.0},
    }
    assert compute_user_cosine_similarity(1, 2, by_user) == 0.0
