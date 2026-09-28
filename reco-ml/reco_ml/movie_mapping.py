"""Resolve source identities without database writes or network requests.

CSV input is kept as text so IMDb leading zeroes are preserved. The caller
supplies catalog entries from the explicit source-ID columns, not JSON metadata.
"""

import csv
import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, TextIO


class MappingConflict(ValueError):
    """Source identities disagree; be careful the caller must not silently merge them."""

class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    MISSING_LINK = "missing_link"
    MISSING_TMDB_ID = "missing_tmdb_id"
    MISSING_CATALOG_MOVIE = "missing_catalog_movie"

@dataclass(frozen=True)
class MovieLink:
    movielens_id: int
    tmdb_id: int | None
    imdb_id: str | None


@dataclass(frozen=True)
class CatalogMovie:
    item_id: int
    tmdb_id: int
    movielens_id: int | None = None
    imdb_id: str | None = None


@dataclass(frozen=True)
class MovieResolution:
    movielens_id: int
    status: ResolutionStatus
    tmdb_id: int | None = None
    item_id: int | None = None
    imdb_id: str | None = None


def _positive_id(value: str, column: str, line: int) -> int:
    if not re.fullmatch(r"[0-9]+", value) or int(value) <= 0:
        raise ValueError(f"Line {line}: invalid {column}: {value!r}")
    return int(value)


def parse_links(source: TextIO) -> dict[int, MovieLink]:
    """Parse links.csv; blank external IDs are missing, malformed IDs are errors.
    Identical duplicate rows are harmless. Contradictory rows and multiple
    MovieLens IDs for one TMDB ID require review under the current schema.
    """
    reader = csv.DictReader(source)
    required = {"movieId", "imdbId", "tmdbId"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("links.csv requires movieId, imdbId and tmdbId columns")
    links: dict[int, MovieLink] = {}
    tmdb_owners: dict[int, int] = {}
    for row in reader:
        line = reader.line_num
        if None in row or any(row[key] is None for key in required):
            raise ValueError(f"Line {line}: malformed CSV row")
        movie_id = _positive_id(row["movieId"].strip(), "movieId", line)
        tmdb_raw = row["tmdbId"].strip()
        imdb_raw = row["imdbId"].strip()
        tmdb_id = _positive_id(tmdb_raw, "tmdbId", line) if tmdb_raw else None
        imdb_id = None
        if imdb_raw:
            _positive_id(imdb_raw, "imdbId", line)
            imdb_id = "tt" + imdb_raw.zfill(7)
        link = MovieLink(movie_id, tmdb_id, imdb_id)
        if movie_id in links and links[movie_id] != link:
            raise MappingConflict(f"Line {line}: conflicting links for MovieLens {movie_id}")
        if tmdb_id is not None:
            owner = tmdb_owners.get(tmdb_id)
            if owner is not None and owner != movie_id:
                raise MappingConflict(f"Line {line}: TMDB {tmdb_id} has multiple MovieLens IDs")
            tmdb_owners[tmdb_id] = movie_id
        links[movie_id] = link
    return links


class MovieResolver:
    """Build indexes once, then resolve each rating's movie ID in constant time."""

    def __init__(self, links: Mapping[int, MovieLink], catalog: Iterable[CatalogMovie]):
        self._links = dict(links)
        self._by_tmdb: dict[int, CatalogMovie] = {}
        self._by_movielens: dict[int, CatalogMovie] = {}
        item_ids: set[int] = set()
        for movie in catalog:
            if movie.item_id <= 0 or movie.tmdb_id <= 0:
                raise ValueError("Catalog item and TMDB IDs must be positive")
            if movie.movielens_id is not None and movie.movielens_id <= 0:
                raise ValueError("Catalog MovieLens IDs must be positive")
            if movie.item_id in item_ids or movie.tmdb_id in self._by_tmdb:
                raise MappingConflict("Duplicate internal or TMDB catalog identity")
            item_ids.add(movie.item_id)
            self._by_tmdb[movie.tmdb_id] = movie
            if movie.movielens_id is not None:
                if movie.movielens_id in self._by_movielens:
                    raise MappingConflict("Duplicate MovieLens catalog identity")
                self._by_movielens[movie.movielens_id] = movie

    def resolve(self, movielens_id: int) -> MovieResolution:
        if movielens_id <= 0:
            raise ValueError("MovieLens ID must be positive")
        link = self._links.get(movielens_id)
        if link is None:
            return MovieResolution(movielens_id, ResolutionStatus.MISSING_LINK)
        if link.movielens_id != movielens_id:
            raise MappingConflict("Link index does not match its MovieLens ID")
        if link.tmdb_id is None:
            return MovieResolution(movielens_id, ResolutionStatus.MISSING_TMDB_ID, imdb_id=link.imdb_id)
        existing = self._by_movielens.get(movielens_id)
        if existing is not None and existing.tmdb_id != link.tmdb_id:
            raise MappingConflict(f"MovieLens {movielens_id}: catalog and links disagree on TMDB ID")
        movie = self._by_tmdb.get(link.tmdb_id)
        if movie is None:
            return MovieResolution(movielens_id, ResolutionStatus.MISSING_CATALOG_MOVIE,
                                   tmdb_id=link.tmdb_id, imdb_id=link.imdb_id)
        if movie.movielens_id is not None and movie.movielens_id != movielens_id:
            raise MappingConflict(f"TMDB {link.tmdb_id}: catalog and links disagree on MovieLens ID")
        if movie.imdb_id and link.imdb_id and movie.imdb_id != link.imdb_id:
            raise MappingConflict(f"TMDB {link.tmdb_id}: catalog and links disagree on IMDb ID")
        return MovieResolution(movielens_id, ResolutionStatus.RESOLVED,
                               tmdb_id=link.tmdb_id, item_id=movie.item_id,
                               imdb_id=link.imdb_id or movie.imdb_id)
