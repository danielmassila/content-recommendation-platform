"""Snapshot parsing and non-destructive loading of external MovieLens ratings."""

import csv
import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError

from psycopg.types.json import Jsonb

from reco_ml.movie_catalog import upsert_tmdb_movie
from reco_ml.movie_mapping import CatalogMovie, MappingConflict, MovieResolver, ResolutionStatus, parse_links


@dataclass(frozen=True)
class ExternalRating:
    user_id: int
    movie_id: int
    rating: Decimal
    rated_at: datetime


def iter_ratings(source):
    reader = csv.DictReader(source)
    required = {'userId', 'movieId', 'rating', 'timestamp'}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError('ratings.csv requires userId, movieId, rating and timestamp')
    for row in reader:
        try:
            if None in row or any(row[key] is None for key in required):
                raise ValueError('Malformed row')
            user, movie = row['userId'].strip(), row['movieId'].strip()
            stamp = row['timestamp'].strip()
            if not all(value.isascii() and value.isdigit() for value in (user, movie, stamp)):
                raise ValueError('Invalid identifier or timestamp')
            user_id, movie_id = int(user), int(movie)
            value = Decimal(row['rating'])
            if user_id <= 0 or movie_id <= 0 or not value.is_finite() or not Decimal('0.5') <= value <= 5 or value * 2 != (value * 2).to_integral_value():
                raise ValueError('Invalid identifier or rating')
            rating = ExternalRating(user_id, movie_id, value, datetime.fromtimestamp(int(stamp), timezone.utc))
        except (ValueError, InvalidOperation, OverflowError, OSError) as error:
            raise ValueError(f'Invalid rating at line {reader.line_num}') from error
        yield reader.line_num, rating


def parse_ratings(source):
    ratings = {}
    for line, rating in iter_ratings(source):
        key = rating.user_id, rating.movie_id
        if key in ratings and ratings[key] != rating:
            raise MappingConflict(f'Conflicting ratings at line {line}')
        ratings[key] = rating
    return list(ratings.values())


def read_snapshot(directory: Path, *, rejected_links=None):
    # Parse exactly the bytes hashed: files cannot change between hashing and parsing.
    content = {name: (directory / name).read_bytes() for name in ('links.csv', 'ratings.csv')}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in content.items()}
    digest = hashlib.sha256(''.join(f'{name}:{hashes[name]}\n' for name in sorted(hashes)).encode()).hexdigest()
    links = parse_links(io.StringIO(content['links.csv'].decode('utf-8-sig')), rejected=rejected_links)
    ratings = parse_ratings(io.StringIO(content['ratings.csv'].decode('utf-8-sig')))
    return f'sha256:{digest}', hashes, links, ratings


def import_snapshot(conn, directory: Path, client=None):
    """Load one snapshot; caller commits or rolls back the complete operation.

    A supplied client may fetch missing catalog movies. Without it, missing
    films are reported for later replay. Only HTTP 404 is a nonfatal API result.
    """
    rejected_links = {}
    version, hashes, links, ratings = read_snapshot(directory, rejected_links=rejected_links)
    catalog = [CatalogMovie(*row) for row in conn.execute(
        "SELECT id, tmdb_id, movielens_id, imdb_id FROM items WHERE type='MOVIE' AND tmdb_id IS NOT NULL"
    ).fetchall()]
    resolver = MovieResolver(links, catalog)
    resolved, rejected = {}, {}
    for movie_id in sorted({rating.movie_id for rating in ratings}):
        if movie_id in rejected_links:
            rejected[movie_id] = rejected_links[movie_id]
            continue
        result = resolver.resolve(movie_id)
        if result.status == ResolutionStatus.MISSING_CATALOG_MOVIE and client is not None:
            try:
                payload = client.get_movie(result.tmdb_id)
            except HTTPError as error:
                if error.code != 404:
                    raise
                rejected[movie_id] = 'tmdb_not_found'
                continue
            if payload.get('id') != result.tmdb_id:
                raise MappingConflict('TMDB response identity differs from links.csv')
            link = links[movie_id]
            if link.imdb_id and payload.get('imdb_id') and link.imdb_id != payload['imdb_id']:
                raise MappingConflict('IMDb identities differ between MovieLens and TMDB')
            item_id = upsert_tmdb_movie(conn, payload)
        elif result.status == ResolutionStatus.RESOLVED:
            item_id = result.item_id
        else:
            rejected[movie_id] = result.status.value
            continue
        link = links[movie_id]
        metadata = {'movieLensId': movie_id, 'source': 'movielens+tmdb'}
        if link.imdb_id:
            metadata['imdbId'] = link.imdb_id
        row = conn.execute("""
            UPDATE items SET movielens_id=%s, imdb_id=COALESCE(imdb_id,%s),
                metadata=COALESCE(metadata,'{}'::jsonb) || %s
            WHERE id=%s AND (movielens_id IS NULL OR movielens_id=%s)
                AND (imdb_id IS NULL OR %s::text IS NULL OR imdb_id=%s)
            RETURNING id
            """, (movie_id, link.imdb_id, Jsonb(metadata), item_id, movie_id, link.imdb_id, link.imdb_id)).fetchone()
        if row is None:
            raise MappingConflict('Catalog identity changed during import')
        resolved[movie_id] = item_id
    inserted = 0
    rejection_counts = Counter()
    for rating in ratings:
        if rating.movie_id not in resolved:
            rejection_counts[rejected[rating.movie_id]] += 1
            continue
        row = conn.execute("""
            INSERT INTO movielens_ratings(dataset_version,movielens_user_id,item_id,rating,rated_at)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING item_id
            """, (version, rating.user_id, resolved[rating.movie_id], rating.rating, rating.rated_at)).fetchone()
        inserted += row is not None
    accepted = len(ratings) - sum(rejection_counts.values())
    return {'dataset_version': version, 'sha256': hashes, 'ratings_read': len(ratings),
            'rejected_links': rejected_links, 'inserted': inserted, 'already_present': accepted - inserted,
            'rejected_ratings': dict(rejection_counts),
            'unresolved_movies': [{'movieId': movie_id, 'reason': reason} for movie_id, reason in rejected.items()]}
