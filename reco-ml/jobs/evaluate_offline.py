from __future__ import annotations

import argparse
import random
from collections import defaultdict
from typing import Dict, List, Tuple, Set

from reco_ml.db import get_db_connection
from reco_ml import repositories
from reco_ml.algo import (
    build_ratings_by_user,
    build_users_by_item,
    compute_profile_maturity_threshold,
    compute_popularity_from_stats,
    recommend_for_user,
    top_p_items,
    compute_bias_terms,
)

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


def main():
    parser = argparse.ArgumentParser(
        description="Offline evaluation with train/test split (per user)"
    )
    parser.add_argument(
        "--split",
        choices=["loo", "ratio"],
        default="loo",
        help="Train/test split method",
    )
    parser.add_argument(
        "--test-ratio", type=float, default=0.2, help="Used only if --split=ratio"
    )
    parser.add_argument(
        "--liked-threshold",
        type=float,
        default=4.0,
        help="For --split=ratio: items with rating >= threshold are considered relevant",
    )
    parser.add_argument(
        "--k", type=int, default=10, help="Evaluate Precision@K, Recall@K, MAP@K"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=50,
        help="How many recommendations to generate per user",
    )
    parser.add_argument("--neighbors", type=int, default=50, help="k-neighbors for CF")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split")
    parser.add_argument(
        "--algo", type=str, default="hybrid_usercf_pop", help="Algo label (for display)"
    )
    parser.add_argument(
        "--pop-top-p",
        type=int,
        default=500,
        help="Top-P popular items used as candidate seed for the hybrid model",
    )
    args = parser.parse_args()

    with get_db_connection() as conn:
        item_ids = repositories.fetch_all_items(conn)
        ratings_all = repositories.fetch_all_ratings(conn)

    train_ratings, test_ratings = split_ratings_by_user(
        ratings=ratings_all,
        method=args.split,
        test_ratio=args.test_ratio,
        seed=args.seed,
    )

    relevant_by_user = build_test_relevant_by_user(
        test_ratings=test_ratings,
        split=args.split,
        liked_threshold=args.liked_threshold,
    )

    ratings_by_user = build_ratings_by_user(train_ratings)
    users_by_item = build_users_by_item(train_ratings)
    mu, b_i, b_u = compute_bias_terms(train_ratings, reg_item=10.0, reg_user=15.0)

    eval_users_list = list(relevant_by_user.keys())

    user_rating_count = {u: len(ratings_by_user.get(u, {})) for u in eval_users_list}

    profile_threshold = compute_profile_maturity_threshold(train_ratings)
    stats_by_item, global_rating = compute_stats_from_ratings(train_ratings)
    pop_scores_all = compute_popularity_from_stats(stats_by_item, global_rating)

    all_items_set = set(item_ids)
    pop_top_items = top_p_items(pop_scores_all, p=args.pop_top_p)

    # Hybrid model wrapper
    def hybrid_reco(u: int):
        return recommend_for_user(
            user_id=u,
            n=args.n,
            k=args.neighbors,
            ratings_by_user=ratings_by_user,
            users_by_item=users_by_item,
            pop_scores_all=pop_scores_all,
            user_rating_count=user_rating_count,
            profile_maturity_threshold=profile_threshold,
            all_items_set=all_items_set,
            pop_top_items=pop_top_items,
            mu=mu,
            b_i=b_i,
            b_u=b_u,
        )

    # For popularity baseline
    def pop_reco(u: int):
        return popularity_recommend_for_user(
            user_id=u,
            n=args.n,
            ratings_by_user=ratings_by_user,
            pop_scores_all=pop_scores_all,
        )

    users_eval_h, p_h, r_h, map_h = eval_model(
        model_name=args.algo,
        users=eval_users_list,
        relevant_by_user=relevant_by_user,
        recommend_fn=hybrid_reco,
        k_eval=args.k,
    )

    users_eval_p, p_p, r_p, map_p = eval_model(
        model_name="popularity",
        users=eval_users_list,
        relevant_by_user=relevant_by_user,
        recommend_fn=pop_reco,
        k_eval=args.k,
    )

    print("")
    print("Offline Evaluation")
    print("------------------")
    print(
        f"split           : {args.split}"
        + (
            f" (test_ratio={args.test_ratio}, liked>={args.liked_threshold})"
            if args.split == "ratio"
            else ""
        )
    )
    print(f"seed            : {args.seed}")
    print(f"users_eval      : {users_eval_h}")
    print(f"ratings_all     : {len(ratings_all)}")
    print(f"train_ratings   : {len(train_ratings)}")
    print(f"test_ratings    : {len(test_ratings)}")
    print("")
    print(
        f"[Popularity baseline] Precision@{args.k}: {p_p:.4f} | Recall@{args.k}: {r_p:.4f} | MAP@{args.k}: {map_p:.4f}"
    )
    print(
        f"[{args.algo}] Precision@{args.k}: {p_h:.4f} | Recall@{args.k}: {r_h:.4f} | MAP@{args.k}: {map_h:.4f}"
    )

    def pct_delta(new: float, old: float) -> float:
        if old == 0:
            return float("inf") if new > 0 else 0.0
        return (new - old) / old * 100.0

    print("")
    print("Delta vs Popularity")
    print("-------------------")
    print(f"Recall@{args.k} : {pct_delta(r_h, r_p):+.1f}%")
    print(f"MAP@{args.k}    : {pct_delta(map_h, map_p):+.1f}%")
    print("")


if __name__ == "__main__":
    main()
