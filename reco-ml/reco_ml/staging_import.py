"""Load rating batches into staging without publishing them.

This module owns commits and requires a dedicated import connection.
"""

import hashlib
import tempfile
import uuid
from itertools import islice
from pathlib import Path

from psycopg import Connection
from reco_ml import ingestion_repository as store

from reco_ml.movielens_csv import iter_ratings


def stage_snapshot(conn: Connection, directory: Path, batch_size: int = 10000) -> dict:
    """Prepare source files, track an attempt and load its rating batches."""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')

    with tempfile.TemporaryDirectory(prefix='movielens-stage-') as temporary:
        snapshot_directory = Path(temporary)
        source_hashes = _copy_source_files(directory, snapshot_directory)
        dataset_version = _dataset_version(source_hashes)
        import_id = uuid.uuid4()
        store.create_import(conn, import_id, dataset_version, source_hashes)
        # Keep the attempt visible even if the first batch fails.
        conn.commit()

        rows_staged = 0
        try:
            with (snapshot_directory / 'ratings.csv').open(encoding='utf-8-sig', newline='') as source:
                ratings = iter_ratings(source)
                while batch := list(islice(ratings, batch_size)):
                    store.write_rating_batch(conn, import_id, batch)
                    rows_staged += len(batch)
                    store.update_progress(conn, import_id, rows_staged)
                    # Commit rows and their progress counter together, never separately.
                    conn.commit()

            # Loading all rows does not make them available to the recommender:
            # only publication can mark the attempt as ready.
            store.mark_staged(conn, import_id)
            conn.commit()
        except BaseException as error:
            # Roll back only the current batch; keep previous batches
            # for diagnosis. A new attempt starts from the beginning.
            conn.rollback()
            store.mark_failed(conn, import_id, type(error).__name__)
            conn.commit()
            raise

    return {
        'import_id': str(import_id),
        'dataset_version': dataset_version,
        'rows_staged': rows_staged,
        'status': 'loading',
        'staging_complete': True,
        'published': False,
    }


def _copy_source_files(source_directory: Path, target_directory: Path) -> dict[str, str]:
    """Copy source files to disk and hash the exact same bytes.

    Source files must remain stable during the copy. Loading then uses
    the copy, independently of later changes to the original files.
    """
    source_hashes = {}
    for filename in ('links.csv', 'ratings.csv'):
        digest = hashlib.sha256()
        with (source_directory / filename).open('rb') as source:
            with (target_directory / filename).open('wb') as target:
                # Bound memory usage independently of file size.
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    target.write(chunk)
        source_hashes[filename] = digest.hexdigest()
    return source_hashes


def _dataset_version(source_hashes: dict[str, str]) -> str:
    """Identify file contents independently of their local path."""
    # Keep this format stable: published versions already use this fingerprint.
    manifest = ''.join(
        f'{filename}:{source_hashes[filename]}\n' for filename in sorted(source_hashes)
    )
    return 'sha256:' + hashlib.sha256(manifest.encode()).hexdigest()
