from __future__ import annotations

import json
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request

from reco_ml.config import get_env
from reco_ml.db import get_db_connection


TMDB_API_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


def _load_metadata(raw_metadata) -> dict:
    if raw_metadata is None:
        return {}

    if isinstance(raw_metadata, dict):
        return raw_metadata

    return json.loads(raw_metadata)


def _request_tmdb_movie(tmdb_id: int, api_key: str, max_attempts: int = 3) -> dict:
    query = urllib.parse.urlencode(
        {
            "api_key": api_key,
            "append_to_response": "credits",
            "language": "fr-FR",
        }
    )
    url = f"{TMDB_API_BASE_URL}/movie/{tmdb_id}?{query}"

    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "content-recommendation-platform/1.0"},
    )
    for attempt in range(max_attempts):
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            is_retryable = error.code == 429 or error.code >= 500
            if not is_retryable or attempt == max_attempts - 1:
                raise
            retry_after = error.headers.get("Retry-After") if error.headers else None
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(delay)

    raise RuntimeError("TMDB request failed without an HTTP response")


def _to_tmdb_metadata(payload: dict) -> dict:
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


def _merge_metadata(current_metadata: dict, tmdb_payload: dict) -> dict:
    tmdb_metadata = _to_tmdb_metadata(tmdb_payload)
    merged = {**current_metadata, **{k: v for k, v in tmdb_metadata.items() if v is not None}}
    merged["source"] = "movielens+tmdb"
    merged["tmdbEnrichedAt"] = datetime.now(timezone.utc).isoformat()
    return merged


def _fetch_items_to_enrich(conn, limit: int) -> list[tuple[int, dict]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, metadata
            FROM items
            WHERE type = 'MOVIE'
              AND metadata ? 'tmdbId'
              AND metadata->>'tmdbId' IS NOT NULL
              AND (
                  NOT (metadata ? 'tmdb')
                  OR NOT (metadata ? 'directors')
                  OR NOT (metadata ? 'cast')
              )
            ORDER BY id
            LIMIT %s;
            """,
            (limit,),
        )
        return [(row[0], _load_metadata(row[1])) for row in cur.fetchall()]


def _update_item_metadata(conn, item_id: int, metadata: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE items
            SET metadata = %s
            WHERE id = %s;
            """,
            (json.dumps(metadata), item_id),
        )


def main() -> None:
    api_key = get_env("TMDB_API_KEY")
    limit = int(get_env("TMDB_ENRICH_LIMIT", "100"))
    delay_seconds = float(get_env("TMDB_REQUEST_DELAY_SECONDS", "0.25"))
    batch_size = max(1, int(get_env("TMDB_ENRICH_BATCH_SIZE", "25")))

    enriched_count = 0
    skipped_count = 0

    with get_db_connection() as conn:
        items = _fetch_items_to_enrich(conn, limit)

        for item_id, metadata in items:
            tmdb_id = metadata.get("tmdbId")

            try:
                payload = _request_tmdb_movie(tmdb_id, api_key)
                enriched_metadata = _merge_metadata(metadata, payload)
                _update_item_metadata(conn, item_id, enriched_metadata)
                enriched_count += 1
                if enriched_count % batch_size == 0:
                    conn.commit()
            except urllib.error.HTTPError as error:
                skipped_count += 1
                print(f"TMDB skip item_id={item_id} tmdb_id={tmdb_id}: HTTP {error.code}")
            except urllib.error.URLError as error:
                skipped_count += 1
                print(f"TMDB skip item_id={item_id} tmdb_id={tmdb_id}: {error.reason}")
            except (ValueError, json.JSONDecodeError) as error:
                skipped_count += 1
                print(f"TMDB skip item_id={item_id} tmdb_id={tmdb_id}: invalid payload ({error})")

            time.sleep(delay_seconds)

        conn.commit()

    print(f"TMDB enrichment DONE | enriched={enriched_count}, skipped={skipped_count}")


if __name__ == "__main__":
    main()
