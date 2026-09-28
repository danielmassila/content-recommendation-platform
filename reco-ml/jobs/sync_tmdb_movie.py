"""Explicit single-film ingestion; requires source-identifier migrations."""

import argparse

from reco_ml.config import get_env
from reco_ml.db import get_db_connection
from reco_ml.movie_catalog import upsert_tmdb_movie
from reco_ml.tmdb_client import TmdbClient


def main():
    parser = argparse.ArgumentParser(description="Create or refresh one TMDB movie")
    parser.add_argument("tmdb_id", type=int)
    args = parser.parse_args()
    # Network calls happen before opening the database transaction.
    payload = TmdbClient(get_env("TMDB_API_KEY")).get_movie(args.tmdb_id)
    with get_db_connection() as conn:
        item_id = upsert_tmdb_movie(conn, payload)
    print(f"Synced tmdb_id={args.tmdb_id} item_id={item_id}")


if __name__ == "__main__":
    main()
