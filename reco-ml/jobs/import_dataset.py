from pathlib import Path
from decimal import Decimal
import json
import re
import pandas as pd

from reco_ml.db import get_db_connection


DATA_DIR = Path("/datasets/raw_data")  # <- ton volume: ./datasets -> /datasets
MOVIES_CSV = DATA_DIR / "movies.csv"
RATINGS_CSV = DATA_DIR / "ratings.csv"
LINKS_CSV = DATA_DIR / "links.csv"


def _extract_year(title: str) -> int | None:
    match = re.search(r"\((\d{4})\)\s*$", title)
    return int(match.group(1)) if match else None


def _format_imdb_id(imdb_id) -> str | None:
    if imdb_id is None or pd.isna(imdb_id):
        return None

    return f"tt{int(imdb_id):07d}"


def main():

    # Read both CSV datasets
    if not MOVIES_CSV.exists():
        raise FileNotFoundError(f"Missing file: {MOVIES_CSV}")
    if not RATINGS_CSV.exists():
        raise FileNotFoundError(f"Missing file: {RATINGS_CSV}")

    movies_df = pd.read_csv(MOVIES_CSV)
    ratings_df = pd.read_csv(RATINGS_CSV)
    links_df = pd.read_csv(LINKS_CSV) if LINKS_CSV.exists() else pd.DataFrame()

    # Safety checks
    movies_cols = {"movieId", "title", "genres"}
    ratings_cols = {"userId", "movieId", "rating"}

    if not movies_cols.issubset(movies_df.columns):
        raise RuntimeError(
            f"movies.csv must contain {movies_cols} (got {set(movies_df.columns)})"
        )

    if not ratings_cols.issubset(ratings_df.columns):
        raise RuntimeError(
            f"ratings.csv must contain {ratings_cols} (got {set(ratings_df.columns)})"
        )

    links_by_movie_id = {}
    if not links_df.empty:
        links_cols = {"movieId", "imdbId", "tmdbId"}
        if not links_cols.issubset(links_df.columns):
            raise RuntimeError(
                f"links.csv must contain {links_cols} (got {set(links_df.columns)})"
            )

        links_by_movie_id = links_df.set_index("movieId").to_dict("index")

    # Generating synthetic users and filling the tables
    user_ids = sorted(ratings_df["userId"].unique().tolist())

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Reset V1 tables
            cur.execute(
                """
                TRUNCATE TABLE ratings, users, items, recommendations
                RESTART IDENTITY CASCADE;
            """
            )

            # users
            user_rows = [(f"user{uid}@example.com",) for uid in user_ids]
            cur.executemany("INSERT INTO users (email) VALUES (%s);", user_rows)

            cur.execute("SELECT id, email FROM users;")
            user_map = {
                int(email.replace("user", "").replace("@example.com", "")): db_id
                for (db_id, email) in cur.fetchall()
            }

            # items (movies)
            item_rows = []
            for row in movies_df.itertuples(index=False):
                external_id = int(row.movieId)
                title = str(row.title)
                genres = str(row.genres) if row.genres is not None else ""
                link = links_by_movie_id.get(external_id, {})
                tmdb_id = link.get("tmdbId")
                imdb_id = link.get("imdbId")
                year = _extract_year(title)

                metadata = {
                    "source": "movielens",
                    "movieLensId": external_id,
                    "imdbId": _format_imdb_id(imdb_id),
                    "tmdbId": None if pd.isna(tmdb_id) else int(tmdb_id),
                    "year": year,
                    "genres": [] if genres == "(no genres listed)" else genres.split("|"),
                }

                item_rows.append((external_id, title, "MOVIE", json.dumps(metadata)))

            cur.executemany(
                """
                INSERT INTO items (external_id, title, type, metadata)
                VALUES (%s, %s, %s, %s);
                """,
                item_rows,
            )

            cur.execute("SELECT id, external_id FROM items;")
            item_map = {int(ext): db_id for (db_id, ext) in cur.fetchall()}

            # ratings
            rating_rows = []
            for row in ratings_df.itertuples(index=False):
                u_ext = int(row.userId)
                i_ext = int(row.movieId)
                rating = Decimal(str(row.rating))

                rating_rows.append((user_map[u_ext], item_map[i_ext], rating))

            cur.executemany(
                """
                INSERT INTO ratings (user_id, item_id, rating)
                VALUES (%s, %s, %s);
                """,
                rating_rows,
            )

            # Information about imported data
            cur.execute("SELECT COUNT(*) FROM users;")
            users_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM items;")
            items_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ratings;")
            ratings_count = cur.fetchone()[0]

    print(
        f"Import DONE | users={users_count}, items={items_count}, ratings={ratings_count}"
    )


if __name__ == "__main__":
    main()
