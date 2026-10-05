"""Stage a snapshot in batches without publishing it to the application."""
import argparse
import json
from pathlib import Path

import psycopg

from reco_ml.config import db_dsn
from reco_ml.staging_import import stage_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--batch-size', type=int, default=10000)
    args = parser.parse_args()
    # Staging owns batch commits so use a dedicated connection.
    with psycopg.connect(db_dsn()) as conn:
        report = stage_snapshot(conn, args.data_dir, args.batch_size)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
