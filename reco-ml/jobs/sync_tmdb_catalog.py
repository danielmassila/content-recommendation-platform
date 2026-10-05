"""Load missing catalogue films referenced by a MovieLens links.csv file."""

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError

import psycopg

from reco_ml.catalog_sync import sync_catalog
from reco_ml.config import db_dsn, get_env
from reco_ml.tmdb_client import TmdbClient


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--links', type=Path, required=True)
    parser.add_argument('--limit', type=int, default=100)
    parser.add_argument('--delay', type=float, default=0.25)
    args = parser.parse_args()
    try:
        client = TmdbClient(get_env('TMDB_API_KEY'))
        with args.links.open(encoding='utf-8-sig', newline='') as source:
            # The synchronizer opens a short transaction for each film.
            with psycopg.connect(db_dsn(), autocommit=True) as conn:
                report = sync_catalog(conn, source, client, limit=args.limit, delay=args.delay)
    except Exception as error:
        # HTTP exception URLs can contain the API key. Never print the exception.
        status = f' HTTP {error.code}' if isinstance(error, HTTPError) else ''
        print(f'Catalogue sync failed: {type(error).__name__}{status}. '
              'Earlier movies remain committed; rerun to resume.', file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
