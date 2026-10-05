"""Offline splitting and ranking metrics; no database access or persisted results."""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Tuple, Set

RatingRow = Tuple[int, int, float]  # (user_id, item_id, rating)


def split_ratings_by_user(
    ratings: List[RatingRow],
    method: str,
    test_ratio: float,
    seed: int,
) -> Tuple[List[RatingRow], List[RatingRow]]:
    rng = random.Random(seed)
    by_user: Dict[int, List[RatingRow]] = defaultdict(list)
    for u, i, r in ratings:
        by_user[u].append((u, i, float(r)))

    train: List[RatingRow] = []
    test: List[RatingRow] = []

    for u, rows in by_user.items():
        if len(rows) < 2:
            continue

        rows = rows[:]
        rng.shuffle(rows)

        if method == "loo":
            test_rows = [rows[0]]
            train_rows = rows[1:]
        elif method == "ratio":
            n_test = max(1, int(round(len(rows) * test_ratio)))
            n_test = min(n_test, len(rows) - 1)
            test_rows = rows[:n_test]
            train_rows = rows[n_test:]
        else:
            raise ValueError("method must be 'loo' or 'ratio'")

        train.extend(train_rows)
        test.extend(test_rows)

    return train, test


def compute_stats_from_ratings(
    ratings: List[RatingRow],
) -> tuple[dict[int, tuple[int, float]], float]:
    if not ratings:
        return {}, 0.0

    sums: Dict[int, float] = defaultdict(float)
    counts: Dict[int, int] = defaultdict(int)

    total_sum = 0.0
    total_count = 0

    for _, item_id, rating in ratings:
        sums[item_id] += float(rating)
        counts[item_id] += 1
        total_sum += float(rating)
        total_count += 1

    stats_by_item = {
        item_id: (counts[item_id], sums[item_id] / counts[item_id])
        for item_id in counts
    }
    global_rating = total_sum / total_count if total_count else 0.0
    return stats_by_item, float(global_rating)


def precision_recall_ap_at_k(
    ranked_items: List[int],
    relevant_items: set[int],
    k: int,
) -> tuple[float, float, float]:
    if k <= 0:
        return 0.0, 0.0, 0.0

    topk = ranked_items[:k]
    if not topk:
        return 0.0, 0.0, 0.0

    hits = 0
    sum_precisions = 0.0

    for idx, item_id in enumerate(topk, start=1):
        if item_id in relevant_items:
            hits += 1
            sum_precisions += hits / idx

    precision = hits / k
    recall = hits / len(relevant_items) if relevant_items else 0.0
    ap = (sum_precisions / len(relevant_items)) if relevant_items else 0.0
    return float(precision), float(recall), float(ap)


def build_test_relevant_by_user(
    test_ratings: List[RatingRow],
    split: str,
    liked_threshold: float,
) -> Dict[int, Set[int]]:
    """
    Build ground truth relevant items per user.

    - split=loo: one held-out item per user => always relevant
    - split=ratio: relevant = items in test with rating >= liked_threshold
    """
    test_by_user: Dict[int, Set[int]] = defaultdict(set)

    if split == "loo":
        for u, i, _r in test_ratings:
            test_by_user[u].add(i)
        return test_by_user

    # ratio
    for u, i, r in test_ratings:
        if float(r) >= liked_threshold:
            test_by_user[u].add(i)

    # Users with no "liked" item in test cannot be evaluated for recall/precision
    test_by_user = {u: items for u, items in test_by_user.items() if items}
    return test_by_user


def popularity_recommend_for_user(
    user_id: int,
    n: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    pop_scores_all: Dict[int, float],
) -> List[Tuple[int, float]]:
    """
    Popularity-only baseline:
    rank items by pop score, excluding already seen items.
    """
    seen = ratings_by_user.get(user_id, {})
    seen_set = set(seen.keys())

    candidates = [
        (item_id, score)
        for item_id, score in pop_scores_all.items()
        if item_id not in seen_set
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:n]


def eval_model(
    *,
    model_name: str,
    users: List[int],
    relevant_by_user: Dict[int, Set[int]],
    recommend_fn,
    k_eval: int,
) -> Tuple[int, float, float, float]:
    """
    recommend_fn(user_id) -> List[(item_id, score)] ranked desc
    Returns: (users_eval, mean_precision, mean_recall, mean_map)
    """
    precisions: List[float] = []
    recalls: List[float] = []
    aps: List[float] = []

    users_eval = 0

    for user_id in users:
        relevant_items = relevant_by_user.get(user_id)
        if not relevant_items:
            continue

        recs = recommend_fn(user_id)
        ranked_items = [item_id for (item_id, _score) in recs]

        p, r, ap = precision_recall_ap_at_k(ranked_items, relevant_items, k_eval)

        precisions.append(p)
        recalls.append(r)
        aps.append(ap)
        users_eval += 1

    def mean(xs: List[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return users_eval, mean(precisions), mean(recalls), mean(aps)

