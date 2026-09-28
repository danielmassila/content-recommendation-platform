"""Import external ratings without resetting application data."""

import argparse
import json
from pathlib import Path

from reco_ml.config import get_env
from reco_ml.db import get_db_connection
from reco_ml.movielens_import import import_snapshot
from reco_ml.tmdb_client import TmdbClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path('/datasets/raw_data'))
    parser.add_argument('--fetch-missing', action='store_true', help='Fetch missing catalog movies from TMDB')
    args = parser.parse_args()
    client = TmdbClient(get_env('TMDB_API_KEY')) if args.fetch_missing else None
    with get_db_connection() as conn:
        report = import_snapshot(conn, args.data_dir, client)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
