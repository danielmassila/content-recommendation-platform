"""Populate the TMDB catalogue from MovieLens links, independently of ratings."""

import math
import time
from urllib.error import HTTPError

from reco_ml.movie_catalog import upsert_tmdb_movie
from reco_ml.movie_mapping import MappingConflict, parse_links


def sync_catalog(conn, source, client, *, limit=100, delay=0.25):
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
    rejected = {}
    links = parse_links(source, rejected=rejected)
    report = dict(synced=0, existing=0, attempted=0, deferred=0,
                  missing_tmdb_id=[], not_found=[], rejected_links=rejected)
    for link in links.values():
        if link.tmdb_id is None:
            report['missing_tmdb_id'].append(link.movielens_id)
            continue
        with conn.transaction():
            existing = conn.execute(
                "SELECT tmdb_id,movielens_id,imdb_id FROM items "
                "WHERE type='MOVIE' AND (tmdb_id=%s OR movielens_id=%s)",
                (link.tmdb_id, link.movielens_id),
            ).fetchall()
            if existing:
                for tmdb_id, movie_id, imdb_id in existing:
                    if (tmdb_id != link.tmdb_id
                            or movie_id not in (None, link.movielens_id)
                            or (imdb_id and link.imdb_id and imdb_id != link.imdb_id)):
                        raise MappingConflict(f'Conflicting catalogue identity for MovieLens {link.movielens_id}')
                report['existing'] += 1
                continue
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
        if payload.get('id') != link.tmdb_id:
            raise MappingConflict('TMDB response does not match the requested identity')
        if payload.get('imdb_id') and link.imdb_id and payload['imdb_id'] != link.imdb_id:
            raise MappingConflict(f'TMDB and links disagree for MovieLens {link.movielens_id}')
        with conn.transaction():
            upsert_tmdb_movie(conn, payload)
        report['synced'] += 1
    return report
