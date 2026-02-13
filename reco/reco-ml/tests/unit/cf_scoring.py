import pytest

from reco_ml.algo import (
    build_ratings_by_user,
    build_users_by_item,
    top_k_similar_users_for_item,
    score_cf,
)


def test_top_k_similar_users_for_item_empty_when_no_raters():
    sims = top_k_similar_users_for_item(
        user_id=1,
        item_id=999,
        ratings_by_user={},
        users_by_item={},
        k=10,
        sim_cache={},
    )
    assert sims == []


def test_top_k_similar_users_filters_self_and_sorts_and_limits():
    ratings = [
        (1, 10, 5.0),
        (1, 20, 1.0),
        (2, 10, 5.0),
        (2, 20, 1.0),
        (3, 10, 5.0),
        (3, 20, 0.0),
        (2, 30, 4.0),
        (3, 30, 2.0),
        (1, 30, 1.0),
    ]
     # user2 identical (sim=1) to user1 on common items but user3 different (0 < sim < 1)
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)

    sims = top_k_similar_users_for_item(
        user_id=1,
        item_id=30,
        ratings_by_user=rbu,
        users_by_item=ubi,
        k=1,
        sim_cache={},
    )

    assert len(sims) == 1
    v_id, sim, v_rating = sims[0]

    assert v_id == 2
    assert sim == pytest.approx(1.0)
    assert v_rating == 4.0


def test_score_cf_returns_zero_if_user_already_rated_item():
    ratings = [(1, 10, 5.0)]
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)

    assert score_cf(
        user_id=1,
        item_id=10,
        ratings_by_user=rbu,
        users_by_item=ubi,
        k=10,
        sim_cache={},
    ) == 0.0


def test_score_cf_weighted_average():
    ratings = [
        (1, 10, 5.0),
        (1, 20, 1.0),
        (2, 10, 5.0),
        (2, 20, 1.0),
        (2, 30, 4.0),
        (3, 10, 5.0),
        (3, 20, 0.0),
        (3, 30, 2.0),
    ]
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)

    sim3 = 25.0 / (math.sqrt(26.0) * 5.0) 
    expected = (1.0 * 4.0 + sim3 * 2.0) / (1.0 + sim3)

    score = score_cf(
        user_id=1,
        item_id=30,
        ratings_by_user=rbu,
        users_by_item=ubi,
        k=10,
        sim_cache={},
    )

    assert score == pytest.approx(expected, rel=1e-9)
