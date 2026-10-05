"""Populate the TMDB catalogue from MovieLens links, independently of ratings."""

import math
import time
from urllib.error import HTTPError
from typing import TextIO

from psycopg import Connection

from reco_ml.movie_catalog import find_movie_identities, upsert_tmdb_movie
from reco_ml.movie_mapping import MappingConflict, MovieLink, parse_links
from reco_ml.tmdb_client import TmdbClient


def sync_catalog(
    conn: Connection,
    source: TextIO,
    client: TmdbClient,
    *,
    limit: int = 100,
    delay: float = 0.25,
) -> dict:
    """Require an autocommit connection; commit each successful movie separately.

    Existing movies are skipped after identity validation. A failed run can be
    repeated: committed movies are not fetched again. 404s are reported and retried
    on the next run; all other errors stop the run, preserving earlier commits.
    """
    if not conn.autocommit:
        raise ValueError('Catalogue sync requires an autocommit connection')
    if type(limit) is not int or limit <= 0:
        raise ValueError('limit must be a positive integer')
    if not math.isfinite(delay) or delay < 0:
        raise ValueError('delay must be finite and non-negative')
    # Quarantine ambiguous links before making any network requests.
    rejected_links = {}
    links = parse_links(source, rejected=rejected_links)
    report = {
        'synced': 0,
        'existing': 0,
        'attempted': 0,
        'deferred': 0,
        'missing_tmdb_id': [],
        'not_found': [],
        'rejected_links': rejected_links,
    }
    for link in links.values():
        if link.tmdb_id is None:
            report['missing_tmdb_id'].append(link.movielens_id)
            continue
        with conn.transaction():
            already_present = _catalogue_contains_movie(conn, link)
        if already_present:
            report['existing'] += 1
            continue

        # Existing films do not consume the request budge but the missing films do.
        if report['attempted'] >= limit:
            report['deferred'] += 1
            continue
        if report['attempted']:
            time.sleep(delay)
        report['attempted'] += 1
        try:
            payload = client.get_movie(link.tmdb_id)
        except HTTPError as error:
            if error.code != 404:
                raise
            report['not_found'].append(link.tmdb_id)
            continue
        _validate_tmdb_identity(link, payload)
        # Each film is committed separately
        with conn.transaction():
            upsert_tmdb_movie(conn, payload)
        report['synced'] += 1
    return report


def _catalogue_contains_movie(conn: Connection, link: MovieLink) -> bool:
    """Skip a film only when its stored identities agree with links.csv."""
    existing_movies = find_movie_identities(
        conn, tmdb_id=link.tmdb_id, movielens_id=link.movielens_id
    )

    for tmdb_id, movielens_id, imdb_id in existing_movies:
        same_tmdb = tmdb_id == link.tmdb_id
        compatible_movielens = movielens_id in (None, link.movielens_id)
        conflicting_imdb = imdb_id and link.imdb_id and imdb_id != link.imdb_id
        if not same_tmdb or not compatible_movielens or conflicting_imdb:
            raise MappingConflict(
                f'Conflicting catalogue identity for MovieLens {link.movielens_id}'
            )

    return bool(existing_movies)


def _validate_tmdb_identity(link: MovieLink, payload: dict) -> None:
    """Never persist a response identifying a different movie from the source link."""
    if payload.get('id') != link.tmdb_id:
        raise MappingConflict('TMDB response does not match the requested identity')

    imdb_id = payload.get('imdb_id')
    if imdb_id and link.imdb_id and imdb_id != link.imdb_id:
        raise MappingConflict(
            f'TMDB and links disagree for MovieLens {link.movielens_id}'
        )
