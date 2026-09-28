from io import StringIO

import pytest

from reco_ml.movie_mapping import (
    CatalogMovie, MappingConflict, MovieResolver, ResolutionStatus, parse_links,
)


def links(rows="2571,0133093,603\n"):
    return parse_links(StringIO("movieId,imdbId,tmdbId\n" + rows))


def test_resolves_three_distinct_ids_without_modifying_tmdb_only_movie():
    movie = CatalogMovie(item_id=125, tmdb_id=603)
    result = MovieResolver(links(), [movie]).resolve(2571)
    assert result.status == ResolutionStatus.RESOLVED
    assert (result.movielens_id, result.tmdb_id, result.item_id) == (2571, 603, 125)
    assert result.imdb_id == "tt0133093"
    assert movie.movielens_id is None


@pytest.mark.parametrize("rows,status,tmdb", [
    ("", ResolutionStatus.MISSING_LINK, None),
    ("2571,0133093,\n", ResolutionStatus.MISSING_TMDB_ID, None),
    ("2571,0133093,603\n", ResolutionStatus.MISSING_CATALOG_MOVIE, 603),
])
def test_missing_mappings_are_explicit(rows, status, tmdb):
    result = MovieResolver(links(rows), []).resolve(2571)
    assert result.status == status
    assert result.item_id is None
    assert result.tmdb_id == tmdb


def test_blank_imdb_and_identical_duplicates_are_supported():
    parsed = links("2571,,603\n2571,,603\n")
    assert len(parsed) == 1
    assert parsed[2571].imdb_id is None


@pytest.mark.parametrize("rows", [
    "2571,0133093,603\n2571,0133093,604\n",
    "2571,0133093,603\n2572,0133093,603\n",
    "2571,0133093,603\n2571,0133094,603\n",
])
def test_conflicting_links_fail_instead_of_overwriting(rows):
    with pytest.raises(MappingConflict):
        links(rows)


@pytest.mark.parametrize("row", [
    "0,0133093,603", "2571,0133093,-1", "2571,0133093,603.5",
    "2571,0133093,NaN", "2571,tt0133093,603", "2571,0133093",
    "2571,0133093,603,extra",
])
def test_invalid_csv_values_are_not_treated_as_missing(row):
    with pytest.raises(ValueError):
        links(row + "\n")


def test_required_headers():
    with pytest.raises(ValueError):
        parse_links(StringIO("movieId,tmdbId\n2571,603\n"))


@pytest.mark.parametrize("movie", [
    CatalogMovie(125, 604, 2571),
    CatalogMovie(125, 603, 999),
    CatalogMovie(125, 603, 2571, "tt9999999"),
])
def test_catalog_conflicts_are_not_silently_repaired(movie):
    with pytest.raises(MappingConflict):
        MovieResolver(links(), [movie]).resolve(2571)


@pytest.mark.parametrize("catalog", [
    [CatalogMovie(1, 603), CatalogMovie(2, 603)],
    [CatalogMovie(1, 603), CatalogMovie(1, 604)],
    [CatalogMovie(1, 603, 2571), CatalogMovie(2, 604, 2571)],
])
def test_duplicate_catalog_identities_fail(catalog):
    with pytest.raises(MappingConflict):
        MovieResolver(links(), catalog)


def test_existing_matching_mapping_is_resolved():
    result = MovieResolver(links(), [CatalogMovie(125, 603, 2571, "tt0133093")]).resolve(2571)
    assert result.item_id == 125


@pytest.mark.parametrize('rows', [
    '1,0000001,603\n2,0000002,603\n3,0000003,604\n',
    '2,0000002,603\n3,0000003,604\n1,0000001,603\n',
])
def test_tolerant_parser_excludes_every_owner_of_ambiguous_tmdb_id(rows):
    rejected = {}
    parsed = parse_links(StringIO('movieId,imdbId,tmdbId\n' + rows), rejected=rejected)
    assert set(parsed) == {3}
    assert rejected == {1: 'ambiguous_link', 2: 'ambiguous_link'}


def test_contradictory_rows_also_quarantine_other_owners():
    rejected = {}
    parsed = parse_links(StringIO('movieId,imdbId,tmdbId\n1,0000001,603\n1,0000001,604\n2,0000002,603\n'), rejected=rejected)
    assert parsed == {}
    assert set(rejected) == {1, 2}
