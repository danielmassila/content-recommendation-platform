"""Bounded-memory COPY loader. Owns transactions on a dedicated connection."""

import hashlib
import tempfile
import uuid
from itertools import islice
from pathlib import Path

from psycopg.types.json import Jsonb

from reco_ml.movielens_csv import iter_ratings


def stage_snapshot(conn, directory: Path, batch_size=10000):
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('batch_size must be a positive integer')
    # Freeze exactly the bytes hashed, on disk rather than in RAM.
    with tempfile.TemporaryDirectory(prefix='movielens-stage-') as temporary:
        hashes = {}
        for name in ('links.csv', 'ratings.csv'):
            digest = hashlib.sha256()
            with (directory / name).open('rb') as source, (Path(temporary) / name).open('wb') as target:
                while chunk := source.read(1024 * 1024):
                    digest.update(chunk)
                    target.write(chunk)
            hashes[name] = digest.hexdigest()
        digest = hashlib.sha256(''.join(f'{name}:{hashes[name]}\n' for name in sorted(hashes)).encode()).hexdigest()
        version = f'sha256:{digest}'
        run_id = uuid.uuid4()
        conn.execute('''INSERT INTO staging.movielens_imports(id,dataset_version,source_hashes)
            VALUES (%s,%s,%s)''', (run_id,version,Jsonb(hashes)))
        conn.commit()
        count = 0
        try:
            with (Path(temporary) / 'ratings.csv').open(encoding='utf-8-sig', newline='') as source:
                rows = iter_ratings(source)
                while batch := list(islice(rows, batch_size)):
                    with conn.cursor() as cur:
                        with cur.copy('''COPY staging.movielens_ratings
                            (import_id,source_line,movielens_user_id,movielens_movie_id,rating,rated_at)
                            FROM STDIN''') as copy:
                            for line, rating in batch:
                                copy.write_row((run_id,line,rating.user_id,rating.movie_id,rating.rating,rating.rated_at))
                        count += len(batch)
                        cur.execute('UPDATE staging.movielens_imports SET rows_read=%s WHERE id=%s',(count,run_id))
                    conn.commit()
            conn.execute('UPDATE staging.movielens_imports SET staged_at=now() WHERE id=%s',(run_id,))
            conn.commit()
        except BaseException as error:
            conn.rollback()
            conn.execute("""UPDATE staging.movielens_imports SET status='failed',finished_at=now(),error_message=%s
                WHERE id=%s""", (type(error).__name__,run_id))
            conn.commit()
            raise
    return {'import_id': str(run_id), 'dataset_version': version, 'rows_staged': count,
            'status': 'loading', 'staging_complete': True, 'published': False}
