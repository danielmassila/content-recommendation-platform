"""Transform TMDB details into the metadata contract used by the application."""

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


def to_tmdb_metadata(payload: dict) -> dict:
    release_date = payload.get("release_date") or None
    year = int(release_date[:4]) if release_date and release_date[:4].isdigit() else None
    credits = payload.get("credits") or {}
    directors = [
        member.get("name")
        for member in credits.get("crew", [])
        if member.get("job") == "Director" and member.get("name")
    ]
    cast = [
        member.get("name")
        for member in credits.get("cast", [])[:12]
        if member.get("name")
    ]

    return {
        "tmdb": {
            "id": payload.get("id"),
            "posterPath": payload.get("poster_path"),
            "backdropPath": payload.get("backdrop_path"),
            "imageBaseUrl": TMDB_IMAGE_BASE_URL,
            "homepage": payload.get("homepage"),
            "popularity": payload.get("popularity"),
            "voteAverage": payload.get("vote_average"),
            "voteCount": payload.get("vote_count"),
        },
        "overview": payload.get("overview"),
        "releaseDate": release_date,
        "runtime": payload.get("runtime"),
        "year": year,
        "genres": [genre["name"] for genre in payload.get("genres", [])],
        "directors": directors,
        "cast": cast,
        "actors": cast,
        "originalLanguage": payload.get("original_language"),
        "originalTitle": payload.get("original_title"),
    }


