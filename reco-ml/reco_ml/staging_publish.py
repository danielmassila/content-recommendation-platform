"""Validate staged notes and publish a complete snapshot atomically."""

import hashlib
import io
import math
from datetime import datetime, timezone

from pathlib import Path
from uuid import UUID

from psycopg import Connection

from reco_ml import ingestion_repository as store
from reco_ml.ingestion_repository import StagedImport
from reco_ml.movie_catalog import fetch_catalog_movies

from reco_ml.movie_mapping import MappingConflict, MovieResolver, ResolutionStatus, parse_links


def publish_snapshot(
    conn: Connection, import_id: UUID, links_path: Path, *, min_coverage: float = 0.95
) -> dict:
    """Validate, resolve and publish an import in the caller's transaction.

    A blocked report performs no final writes. Exceptions require rollback.
    The caller commits accepted ratings and readiness together.
    """
    if not math.isfinite(min_coverage) or not 0 <= min_coverage <= 1:
        raise ValueError('min_coverage must be finite and between 0 and 1')

    attempt = store.load_locked_import(conn, import_id)
    if attempt.status == 'ready':
        return {
            'import_id': str(import_id),
            'dataset_version': attempt.dataset_version,
            'already_published': True,
        }

    _require_publishable_import(conn, attempt)
    links, rejected_links = _read_matching_links(
        links_path, attempt.source_hashes.get('links.csv')
    )

    # Keep both sides of the mapping stable until publication commits or rolls back.
    store.lock_publication_sources(conn)
    source_rows = _validate_staged_ratings(conn, import_id, attempt.rows_read)
    _build_publication_mapping(conn, import_id, links, rejected_links)

    report = _coverage_report(
        import_id, attempt.dataset_version, source_rows,
        store.count_rejections(conn, import_id), min_coverage,
    )
    if report.get('status') == 'blocked':
        return report

    # These writes share one transaction: readers must never see a partial publication.
    published = store.replace_published_ratings(conn, import_id, attempt.dataset_version)
    store.mark_import_ready(
        conn, import_id, report['accepted_source_rows'], sum(report['rejected_ratings'].values())
    )
    report.update(
        published=published,
        duplicate_rows=report['accepted_source_rows'] - published,
        status='ready',
    )
    return report


def _require_publishable_import(conn: Connection, attempt: StagedImport) -> None:
    """Require completed staging and serialize attempts for the same dataset."""
    if attempt.status != 'loading' or attempt.staged_at is None:
        raise ValueError('Import has not completed staging')
    store.lock_dataset(conn, attempt.dataset_version)
    published_attempt = store.is_dataset_published(conn, attempt.dataset_version)
    if published_attempt:
        raise ValueError('Snapshot already published by another attempt')


def _coverage_report(
    import_id: UUID, dataset_version: str, source_rows: int,
    rejected_ratings: dict[str, int], min_coverage: float,
) -> dict:
    """Apply the acceptance rule to source rows, including identical duplicates."""
    accepted_rows = source_rows - sum(rejected_ratings.values())
    coverage = accepted_rows / source_rows
    report = {
        'import_id': str(import_id),
        'dataset_version': dataset_version,
        'validated_at': datetime.now(timezone.utc).isoformat(),
        'source_rows': source_rows,
        'accepted_source_rows': accepted_rows,
        'coverage': coverage,
        'min_coverage': min_coverage,
        'rejected_ratings': rejected_ratings,
    }
    if accepted_rows == 0:
        report.update(status='blocked', reason='no_resolved_ratings')
    elif coverage < min_coverage:
        report.update(status='blocked', reason='insufficient_coverage')
    return report


def _read_matching_links(links_path: Path, expected_hash: str | None):
    """Reject changed sources before resolving any movie identities."""
    data = links_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise ValueError('links.csv differs from the staged snapshot')
    rejected = {}
    links = parse_links(io.StringIO(data.decode('utf-8-sig')), rejected=rejected)
    return links, rejected


def _validate_staged_ratings(conn: Connection, import_id: UUID, expected_rows: int) -> int:
    """Require a complete, non-empty import without conflicting user/movie notes."""
    count = store.count_staged_ratings(conn, import_id)
    if count != expected_rows or count == 0:
        raise ValueError('Staging is empty or row count differs from progress')
    conflict = store.find_conflicting_rating(conn, import_id)
    if conflict:
        raise MappingConflict(f'Conflicting staged ratings for user/movie {conflict}')
    return count


def _build_publication_mapping(conn, import_id, links, rejected) -> None:
    """Resolve each distinct source movie once; SQL will join all its ratings.

    The temporary mapping disappears when the caller commits or rolls back.
    """
    resolver = MovieResolver(links, fetch_catalog_movies(conn))
    movies = store.fetch_staged_movie_ids(conn, import_id)

    def mapping_rows():
        for movie_id in movies:
            if movie_id in rejected:
                yield movie_id, None, rejected[movie_id]
                continue
            result = resolver.resolve(movie_id)
            reason = None if result.status == ResolutionStatus.RESOLVED else result.status.value
            yield movie_id, result.item_id, reason

    store.write_publication_mapping(conn, mapping_rows())
