"""Compute recommendations for all application users or one selected account."""

import argparse
import time

from reco_ml.algo import recompute_all_recommendations, recompute_user_recommendations
from reco_ml.db import get_db_connection
from reco_ml.recommendation_options import CLI_RECOMMENDATION_DEFAULTS, RecommendationOptions


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute offline recommendations")
    parser.add_argument(
        "--n", type=int, default=CLI_RECOMMENDATION_DEFAULTS.n_per_user, help="Number of recommendations per user"
    )
    parser.add_argument(
        "--user-id",
        type=int,
        help="Recompute only this user, preserving every other user's recommendations",
    )
    parser.add_argument("--k", type=int, default=CLI_RECOMMENDATION_DEFAULTS.k_neighbors, help="Number of neighbors for CF")
    parser.add_argument(
        "--algo",
        type=str,
        default=CLI_RECOMMENDATION_DEFAULTS.algo_version,
        help="Algorithm version label stored in DB",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run sanity checks after recomputation (counts, top users)",
    )

    parser.add_argument("--dataset-version", help="Exact MovieLens snapshot to use as external neighbors")
    args = parser.parse_args()

    start = time.perf_counter()

    with get_db_connection() as conn:
        # Both modes use the same corpus and algorithm settings.
        options = RecommendationOptions(
            n_per_user=args.n,
            k_neighbors=args.k,
            algo_version=args.algo,
            dataset_version=args.dataset_version,
        )
        if args.user_id is None:
            recompute_all_recommendations(conn, options=options)
        else:
            recompute_user_recommendations(conn, user_id=args.user_id, options=options)

        end = time.perf_counter()
        duration = end - start
        print(f"\nRecomputation finished in {duration:.2f} seconds")

        if args.check:
            _print_recommendation_counts(conn)


def _print_recommendation_counts(conn) -> None:
    """Display a small sanity check, not a recommendation-quality evaluation."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM recommendations;")
        print("recommendations rows:", cursor.fetchone()[0])
        cursor.execute(
            """
            SELECT user_id, COUNT(*)
            FROM recommendations
            GROUP BY user_id
            ORDER BY COUNT(*) DESC
            LIMIT 5;
            """
        )
        print("top users by #recs:", cursor.fetchall())


if __name__ == "__main__":
    main()
