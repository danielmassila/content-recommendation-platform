from reco_ml.algo import (
    build_ratings_by_user,
    build_users_by_item,
    compute_profile_maturity_threshold,
    compute_bias_terms,
    recommend_for_user,
    top_p_items,
)


def test_recommend_for_user_excludes_seen_items_and_returns_sorted():
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

    ratings_by_user = build_ratings_by_user(ratings)
    users_by_item = build_users_by_item(ratings)

    user_rating_count = {1: 2, 2: 3, 3: 3}
    threshold = compute_profile_maturity_threshold(ratings)

    # mocked popularity
    pop_scores_all = {10: 0.1, 20: 0.2, 30: 0.9, 40: 0.8}

    all_items_set = {10, 20, 30, 40}
    pop_top_items = top_p_items(pop_scores_all, p=4)

    mu, b_i, b_u = compute_bias_terms(ratings, reg_item=10.0, reg_user=15.0)

    recs = recommend_for_user(
        user_id=1,
        n=2,
        k=10,
        ratings_by_user=ratings_by_user,
        users_by_item=users_by_item,
        pop_scores_all=pop_scores_all,
        user_rating_count=user_rating_count,
        profile_maturity_threshold=threshold,
        all_items_set=all_items_set,
        pop_top_items=pop_top_items,
        mu=mu,
        b_i=b_i,
        b_u=b_u,
    )

    # user 1 already saw 10 and 20
    rec_items = [i for (i, _) in recs]
    assert 10 not in rec_items
    assert 20 not in rec_items

    # sorted recommendations
    assert len(recs) == 2
    assert recs[0][1] >= recs[1][1]
