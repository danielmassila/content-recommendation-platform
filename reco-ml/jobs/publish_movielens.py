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
    args = parser.parse_args()
    with get_db_connection() as conn:
        report = publish_snapshot(conn,args.import_id,args.links)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
