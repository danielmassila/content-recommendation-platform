"""Validate staged notes and publish a complete snapshot atomically."""

import hashlib
import io
import math
from datetime import datetime, timezone

from pathlib import Path

from reco_ml.movie_mapping import CatalogMovie, MappingConflict, MovieResolver, ResolutionStatus, parse_links


def publish_snapshot(conn, import_id, links_path: Path, *, min_coverage=0.95):
    """Caller owns commit/rollback. No HTTP calls and no partial publication.

    Missing/ambiguous mappings are rejected and counted. Conflicting notes fail
    the entire publication. Coverage refusals return a blocked report: callers
    should print it and report failure to the user. No report is stored in DB.
    Structural validation errors raise and leave staging available for review.
    """
    if not math.isfinite(min_coverage) or not 0 <= min_coverage <= 1:
        raise ValueError('min_coverage must be finite and between 0 and 1')
    conn.execute("SET LOCAL lock_timeout = '5s'")
    row = conn.execute('''SELECT dataset_version,status,source_hashes,rows_read,staged_at
        FROM staging.movielens_imports WHERE id=%s FOR UPDATE''',(import_id,)).fetchone()
    if row is None:
        raise ValueError('Unknown import')
    version, status, hashes, expected, staged_at = row
    if status == 'ready':
        return {'import_id': str(import_id), 'dataset_version': version, 'already_published': True}
    if status != 'loading' or staged_at is None:
        raise ValueError('Import has not completed staging')
    # Serialize publications for a snapshot, including attempts with different UUIDs.
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(version,))
    if conn.execute("SELECT 1 FROM staging.movielens_imports WHERE dataset_version=%s AND status='ready'",(version,)).fetchone():
        raise ValueError('Snapshot already published by another attempt')
    data = links_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != hashes.get('links.csv'):
        raise ValueError('links.csv differs from the staged snapshot')
    rejected = {}
    links = parse_links(io.StringIO(data.decode('utf-8-sig')), rejected=rejected)
    # Keep source rows and catalogue mappings stable throughout validation/publication.
    conn.execute('LOCK TABLE staging.movielens_ratings IN SHARE MODE')
    conn.execute('LOCK TABLE items IN SHARE MODE')
    count = conn.execute('SELECT count(*) FROM staging.movielens_ratings WHERE import_id=%s',(import_id,)).fetchone()[0]
    if count != expected or count == 0:
        raise ValueError('Staging is empty or row count differs from progress')
    conflict = conn.execute('''SELECT movielens_user_id,movielens_movie_id
        FROM staging.movielens_ratings WHERE import_id=%s
        GROUP BY movielens_user_id,movielens_movie_id
        HAVING count(DISTINCT (rating,rated_at)) > 1 LIMIT 1''',(import_id,)).fetchone()
    if conflict:
        raise MappingConflict(f'Conflicting staged ratings for user/movie {conflict}')
    catalog = [CatalogMovie(*row) for row in conn.execute("SELECT id,tmdb_id,movielens_id,imdb_id FROM items WHERE type='MOVIE' AND tmdb_id IS NOT NULL")]
    resolver = MovieResolver(links,catalog)
    conn.execute('CREATE TEMP TABLE publication_mapping(movie_id BIGINT PRIMARY KEY,item_id BIGINT,reason TEXT) ON COMMIT DROP')
    movies = conn.execute('SELECT DISTINCT movielens_movie_id FROM staging.movielens_ratings WHERE import_id=%s',(import_id,)).fetchall()
    with conn.cursor() as cur:
        with cur.copy('COPY publication_mapping FROM STDIN') as copy:
            for (movie_id,) in movies:
                if movie_id in rejected:
                    copy.write_row((movie_id,None,rejected[movie_id]))
                    continue
                result = resolver.resolve(movie_id)
                copy.write_row((movie_id,result.item_id,None if result.status == ResolutionStatus.RESOLVED else result.status.value))
    rejection_counts = dict(conn.execute('''SELECT m.reason,count(*) FROM staging.movielens_ratings s
        JOIN publication_mapping m ON m.movie_id=s.movielens_movie_id
        WHERE s.import_id=%s AND m.item_id IS NULL GROUP BY m.reason''',(import_id,)).fetchall())
    accepted = count - sum(rejection_counts.values())
    report = {
        'import_id': str(import_id), 'dataset_version': version,
        'validated_at': datetime.now(timezone.utc).isoformat(),
        'source_rows': count, 'accepted_source_rows': accepted,
        'coverage': accepted / count, 'min_coverage': min_coverage,
        'rejected_ratings': rejection_counts,
    }
    if accepted == 0 or accepted / count < min_coverage:
        report.update(status='blocked', reason='no_resolved_ratings' if accepted == 0 else 'insufficient_coverage')
        return report

    # Replace only this snapshot; other snapshots and application tables are untouched.
    conn.execute('DELETE FROM public.movielens_ratings WHERE dataset_version=%s',(version,))
    result = conn.execute('''INSERT INTO public.movielens_ratings
        (dataset_version,movielens_user_id,item_id,rating,rated_at)
        SELECT DISTINCT %s,s.movielens_user_id,m.item_id,s.rating,s.rated_at
        FROM staging.movielens_ratings s JOIN publication_mapping m ON m.movie_id=s.movielens_movie_id
        WHERE s.import_id=%s AND m.item_id IS NOT NULL''',(version,import_id))
    published = result.rowcount
    report.update(published=published, duplicate_rows=accepted-published, status='ready')
    conn.execute("""UPDATE staging.movielens_imports SET status='ready',finished_at=now(),
        rows_accepted=%s,rows_rejected=%s WHERE id=%s""",
        (accepted,count-accepted,import_id))
    return report
