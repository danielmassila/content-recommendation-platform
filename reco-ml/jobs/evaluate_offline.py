"""Compare hybrid recommendations with popularity using application ratings only."""

from __future__ import annotations

import argparse

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

from reco_ml.evaluation import (
    split_ratings_by_user,
    compute_stats_from_ratings,
    build_test_relevant_by_user,
    popularity_recommend_for_user,
    eval_model,
)


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

    # This evaluates application ratings only, not the external MovieLens corpus.
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

    # Build statistics from training data only to avoid leaking held-out ratings.
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
