"""Validate and publish a staged MovieLens attempt."""
import argparse
import json
from pathlib import Path
from uuid import UUID

from reco_ml.db import get_db_connection
from reco_ml.staging_publish import publish_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-id', type=UUID, required=True)
    parser.add_argument('--links', type=Path, required=True)
    parser.add_argument('--min-coverage', type=float, default=0.95,
                        help='Minimum fraction of source rating rows resolved (default: 0.95)')
    args = parser.parse_args()
    with get_db_connection() as conn:
        report = publish_snapshot(conn,args.import_id,args.links,min_coverage=args.min_coverage)
    print(json.dumps(report,indent=2))
    return 1 if report.get("status") == "blocked" else 0


if __name__ == '__main__':
    raise SystemExit(main())
