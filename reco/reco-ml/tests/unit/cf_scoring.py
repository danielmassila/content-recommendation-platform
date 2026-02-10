import pytest
from reco_ml.algo import build_ratings_by_user, build_users_by_item, top_k_similar_users_for_item, score_cf


def test_top_k_similar_users_for_item_empty_when_no_raters():
    assert top_k_similar_users_for_item(
        user_id=1,
        item_id=999,
        ratings_by_user={},
        users_by_item={},
        k=10,
    ) == []


def test_top_k_similar_users_filters_self_and_sorts_and_limits():
    ratings = [
        (1, 10, 5.0), (1, 20, 1.0),
        (2, 10, 5.0), (2, 20, 1.0),  # user2 identical => sim=1
        (3, 10, 5.0), (3, 20, 0.0),  # user3 slightly different => sim<1 but >0
        (2, 30, 4.0),
        (3, 30, 2.0),
    ]
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)

    sims = top_k_similar_users_for_item(
        user_id=1,
        item_id=30,
        ratings_by_user=rbu,
        users_by_item=ubi,
        k=1,
    )
    assert len(sims) == 1
    assert sims[0][0] == 2  # user2 should be most similar
    assert sims[0][1] == pytest.approx(1.0)
    assert sims[0][2] == 4.0  # rating on item 30


def test_score_cf_returns_zero_if_user_already_rated_item():
    ratings = [(1, 10, 5.0)]
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)
    assert score_cf(1, 10, rbu, ubi, k=10) == 0.0


def test_score_cf_weighted_average():
    # user1 wants item 30
    # user2 similar=1 rates 4
    # user3 similar=0.5 rates 2
    ratings = [
        (1, 10, 5.0), (1, 20, 1.0),
        (2, 10, 5.0), (2, 20, 1.0), (2, 30, 4.0),
        (3, 10, 5.0), (3, 20, 0.0), (3, 30, 2.0),
    ]
    rbu = build_ratings_by_user(ratings)
    ubi = build_users_by_item(ratings)

    score = score_cf(1, 30, rbu, ubi, k=10)
    # (1*4 + 0.5*2) / (1+0.5) = (4+1)/1.5 = 3.333...
    assert score == pytest.approx(3.3333333333, rel=1e-6)
