"""MovieLens rating parsing shared by staging and source validation."""

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


from reco_ml.movie_mapping import MappingConflict, parse_links


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
