"""MovieLens ingestion SQL. Callers own transactions, commits and rollbacks."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from psycopg import Connection
from psycopg.types.json import Jsonb

from reco_ml.movielens_csv import ExternalRating

@dataclass(frozen=True)
class StagedImport:
    """The persisted facts needed to validate one import attempt."""

    dataset_version: str
    status: str
    source_hashes: dict[str, str]
    rows_read: int
    staged_at: datetime | None


def load_locked_import(conn: Connection, import_id: UUID) -> StagedImport:
    """Prevent concurrent publication of the same attempt."""
    conn.execute("SET LOCAL lock_timeout = '5s'")
    row = conn.execute(
        """
        SELECT dataset_version, status, source_hashes, rows_read, staged_at
        FROM staging.movielens_imports
        WHERE id = %s FOR UPDATE
        """,
        (import_id,),
    ).fetchone()
    if row is None:
        raise ValueError('Unknown import')
    return StagedImport(*row)


def mark_import_ready(
    conn: Connection, import_id: UUID, accepted_rows: int, rejected_rows: int
) -> None:
    """Record final counters without committing independently of the ratings."""
    conn.execute(
        """
        UPDATE staging.movielens_imports
        SET status='ready', finished_at=now(), rows_accepted=%s, rows_rejected=%s
        WHERE id=%s
        """,
        (accepted_rows, rejected_rows, import_id),
    )


def replace_published_ratings(conn: Connection, import_id: UUID, version: str) -> int:
    """Replace this version only, within the caller's publication transaction."""
    # Replace only this snapshot; other snapshots and application tables are untouched.
    conn.execute('DELETE FROM public.movielens_ratings WHERE dataset_version=%s',(version,))
    result = conn.execute('''INSERT INTO public.movielens_ratings
        (dataset_version,movielens_user_id,item_id,rating,rated_at)
        SELECT DISTINCT %s,s.movielens_user_id,m.item_id,s.rating,s.rated_at
        FROM staging.movielens_ratings s JOIN publication_mapping m ON m.movie_id=s.movielens_movie_id
        WHERE s.import_id=%s AND m.item_id IS NOT NULL''',(version,import_id))
    published = result.rowcount
    return published


def count_rejections(conn: Connection, import_id: UUID) -> dict[str, int]:
    """Count rejected source rows, including duplicates, rather than unique films."""
    return dict(conn.execute(
        """
        SELECT mapping.reason, count(*)
        FROM staging.movielens_ratings AS ratings
        JOIN publication_mapping AS mapping
            ON mapping.movie_id = ratings.movielens_movie_id
        WHERE ratings.import_id = %s AND mapping.item_id IS NULL
        GROUP BY mapping.reason
        """,
        (import_id,),
    ).fetchall())

def write_rating_batch(
    conn: Connection,
    import_id: UUID,
    batch: list[tuple[int, ExternalRating]],
) -> None:
    """Write a batch with COPY; stage_snapshot remains responsible for committing."""
    with conn.cursor() as cursor:
        with cursor.copy(
            """
            COPY staging.movielens_ratings
                (import_id, source_line, movielens_user_id, movielens_movie_id, rating, rated_at)
            FROM STDIN
            """
        ) as copy:
            for source_line, rating in batch:
                copy.write_row((
                    import_id,
                    source_line,
                    rating.user_id,
                    rating.movie_id,
                    rating.rating,
                    rating.rated_at,
                ))

def create_import(conn, import_id, dataset_version, source_hashes):
    conn.execute(
        'INSERT INTO staging.movielens_imports (id,dataset_version,source_hashes) VALUES (%s,%s,%s)',
        (import_id, dataset_version, Jsonb(source_hashes)),
    )


def update_progress(conn, import_id, rows_staged):
    conn.execute('UPDATE staging.movielens_imports SET rows_read=%s WHERE id=%s', (rows_staged, import_id))


def mark_staged(conn, import_id):
    conn.execute('UPDATE staging.movielens_imports SET staged_at=now() WHERE id=%s', (import_id,))


def mark_failed(conn, import_id, error_name):
    conn.execute(
        "UPDATE staging.movielens_imports SET status='failed',finished_at=now(),error_message=%s WHERE id=%s",
        (error_name, import_id),
    )


def lock_publication_sources(conn):
    """Keep source notes and catalogue identities stable until the transaction ends."""
    conn.execute('LOCK TABLE staging.movielens_ratings IN SHARE MODE')
    conn.execute('LOCK TABLE items IN SHARE MODE')


def lock_dataset(conn, dataset_version):
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', (dataset_version,))


def is_dataset_published(conn, dataset_version) -> bool:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT 1 FROM staging.movielens_imports WHERE dataset_version=%s AND status='ready')",
            (dataset_version,),
        )
        return cursor.fetchone()[0]


def count_staged_ratings(conn, import_id) -> int:
    return conn.execute('SELECT count(*) FROM staging.movielens_ratings WHERE import_id=%s', (import_id,)).fetchone()[0]


def find_conflicting_rating(conn, import_id):
    return conn.execute(
        """
        SELECT movielens_user_id, movielens_movie_id
        FROM staging.movielens_ratings WHERE import_id=%s
        GROUP BY movielens_user_id, movielens_movie_id
        HAVING count(DISTINCT (rating,rated_at)) > 1 LIMIT 1
        """, (import_id,),
    ).fetchone()


def fetch_staged_movie_ids(conn, import_id) -> list[int]:
    return [row[0] for row in conn.execute(
        'SELECT DISTINCT movielens_movie_id FROM staging.movielens_ratings WHERE import_id=%s',
        (import_id,),
    ).fetchall()]


def write_publication_mapping(conn, rows):
    """Create a transaction-local mapping and consume resolved rows incrementally."""
    conn.execute('CREATE TEMP TABLE publication_mapping(movie_id BIGINT PRIMARY KEY,item_id BIGINT,reason TEXT) ON COMMIT DROP')
    with conn.cursor() as cursor:
        with cursor.copy('COPY publication_mapping FROM STDIN') as copy:
            for row in rows:
                copy.write_row(row)


def fetch_published_ratings(conn, dataset_version):
    with conn.cursor() as cursor:
        cursor.execute(
            'SELECT movielens_user_id,item_id,rating FROM movielens_ratings WHERE dataset_version=%s',
            (dataset_version,),
        )
        return cursor.fetchall()
