import argparse

from reco_ml.algo import recompute_all_recommendations
from reco_ml.db import get_db_connection


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute offline recommendations")
    parser.add_argument("--n", type=int, default=20, help="Number of recommendations per user")
    parser.add_argument("--k", type=int, default=50, help="Number of neighbors for CF")
    parser.add_argument(
        "--algo",
        type=str,
        default="hybrid_usercf_pop",
        help="Algorithm version label stored in DB",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run sanity checks after recomputation (counts, top users)",
    )

    args = parser.parse_args()

    with get_db_connection() as conn:
        recompute_all_recommendations(
            conn,
            n_per_user=args.n,
            k_neighbors=args.k,
            algo_version=args.algo,
        )

        if args.check:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM recommendations;")
                total = cur.fetchone()[0]
                print("recommendations rows:", total)

                cur.execute(
                    """
                    SELECT user_id, COUNT(*)
                    FROM recommendations
                    GROUP BY user_id
                    ORDER BY COUNT(*) DESC
                    LIMIT 5;
                    """
                )
                print("top users by #recs:", cur.fetchall())


if __name__ == "__main__":
    main()
