from reco_ml.algo import recompute_all_recommendations
from reco_ml.repositories import RecommendationRow


def test_recompute_all_recommendations_writes_rows(monkeypatch):
    user_ids = [1, 2]
    item_ids = [10, 20, 30]
    ratings = [
        (1, 10, 5.0),
        (2, 20, 4.0),
        (2, 30, 2.0),
    ]
    stats_by_items = {
        10: (10, 4.0),
        20: (5, 3.0),
        30: (2, 2.0),
    }
    global_rating = 3.5

    captured = {"rows": None}

    monkeypatch.setattr(
        "reco_ml.algo.repositories.fetch_all_users", lambda _conn: user_ids
    )
    monkeypatch.setattr(
        "reco_ml.algo.repositories.fetch_all_items", lambda _conn: item_ids
    )
    monkeypatch.setattr(
        "reco_ml.algo.repositories.fetch_all_ratings", lambda _conn: ratings
    )
    monkeypatch.setattr(
        "reco_ml.algo.repositories.get_stats_by_item", lambda _conn: stats_by_items
    )
    monkeypatch.setattr(
        "reco_ml.algo.repositories.get_global_rating", lambda _conn: global_rating
    )

    def fake_write(_conn, rows):
        captured["rows"] = list(rows)

    monkeypatch.setattr("reco_ml.algo.repositories.write_recommendations", fake_write)

    def fake_recommend_for_user(
        user_id: int,
        n: int,
        k: int,
        item_list: list[int],
        ratings_by_user: dict[int, dict[int, float]],
        users_by_item: dict[int, dict[int, float]],
        pop_scores_all: dict[int, float],
        user_rating_count: dict[int, int],
        profile_maturity_threshold: int,
    ):
        if user_id == 1:
            return [(20, 0.9), (30, 0.8)][:n]
        if user_id == 2:
            return [(10, 0.7)][:n]
        return []

    monkeypatch.setattr("reco_ml.algo.recommend_for_user", fake_recommend_for_user)

    recompute_all_recommendations(
        conn=object(),
        n_per_user=2,
        k_neighbors=50,
        algo_version="test_algo",
    )

    rows = captured["rows"]
    assert rows is not None
    assert all(isinstance(r, RecommendationRow) for r in rows)

    assert len(rows) == 3
    assert all(r.algo_version == "test_algo" for r in rows)

    by_user: dict[int, list[RecommendationRow]] = {}
    for r in rows:
        by_user.setdefault(r.user_id, []).append(r)

    assert sorted([r.rank for r in by_user[1]]) == [1, 2]
    assert sorted([r.rank for r in by_user[2]]) == [1]

    user1_items_by_rank = [r.item_id for r in sorted(by_user[1], key=lambda x: x.rank)]
    user2_items_by_rank = [r.item_id for r in sorted(by_user[2], key=lambda x: x.rank)]
    assert user1_items_by_rank == [20, 30]
    assert user2_items_by_rank == [10]
