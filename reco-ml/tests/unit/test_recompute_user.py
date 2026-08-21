from reco_ml import algo
from reco_ml.repositories import RecommendationRow


def test_recompute_user_writes_only_target_user(monkeypatch):
    monkeypatch.setattr(algo.repositories, "fetch_all_users", lambda conn: [1, 2])
    monkeypatch.setattr(algo.repositories, "fetch_all_items", lambda conn: [10, 20])
    monkeypatch.setattr(
        algo.repositories,
        "fetch_all_item_profiles",
        lambda conn: {10: {"title": "A", "metadata": {}}, 20: {"title": "B", "metadata": {}}},
    )
    monkeypatch.setattr(algo.repositories, "fetch_user_preferences", lambda conn: {})
    monkeypatch.setattr(
        algo.repositories,
        "fetch_all_ratings",
        lambda conn: [(1, 10, 5.0), (2, 10, 4.0), (2, 20, 5.0)],
    )
    monkeypatch.setattr(
        algo.repositories,
        "get_stats_by_item",
        lambda conn: {10: (2, 4.5), 20: (1, 5.0)},
    )
    monkeypatch.setattr(algo.repositories, "get_global_rating", lambda conn: 4.6)
    captured = {}

    def write_user(conn, user_id, rows):
        captured["user_id"] = user_id
        captured["rows"] = list(rows)

    monkeypatch.setattr(algo.repositories, "write_user_recommendations", write_user)

    algo.recompute_user_recommendations(object(), user_id=1, n_per_user=5)

    assert captured["user_id"] == 1
    assert all(isinstance(row, RecommendationRow) for row in captured["rows"])
    assert all(row.user_id == 1 for row in captured["rows"])
    assert all(row.item_id != 10 for row in captured["rows"])


def test_recompute_user_rejects_unknown_user(monkeypatch):
    monkeypatch.setattr(algo.repositories, "fetch_all_users", lambda conn: [1])

    try:
        algo.recompute_user_recommendations(object(), user_id=999)
    except ValueError as error:
        assert str(error) == "Unknown user id: 999"
    else:
        raise AssertionError("Expected unknown user to be rejected")
