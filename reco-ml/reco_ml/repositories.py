from typing import Iterable, List
from decimal import Decimal
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecommendationRow:
    user_id: int
    item_id: int
    score: float
    algo_version: str
    rank: int


def fetch_all_users(conn) -> List[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users;")
        return [row[0] for row in cur.fetchall()]


def fetch_all_items(conn) -> List[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM items;")
        return [row[0] for row in cur.fetchall()]


def fetch_all_ratings(conn) -> List[tuple[int, int, float]]:
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, item_id, rating FROM ratings;")
        return [(row[0], row[1], float(row[2])) for row in cur.fetchall()]


def write_recommendations(conn, rows: Iterable[RecommendationRow]) -> None:
    infos = [(r.user_id, r.item_id, r.score, r.algo_version, r.rank) for r in rows]
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE recommendations RESTART IDENTITY;")
        cur.executemany(
            """
            INSERT INTO recommendations (user_id, item_id, score, algo_version, rank)
            VALUES (%s, %s, %s, %s, %s);
            """,
            infos,
        )


def get_stats_by_item(conn) -> dict[int, tuple[int, float]]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT item_id, COUNT(*) AS v, AVG(rating) AS r
            FROM ratings
            GROUP BY item_id;
            """
        )
        return {row[0]: (row[1], float(row[2])) for row in cur.fetchall()}


def get_global_rating(conn) -> float:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT AVG(rating)
            FROM ratings;
            """
        )
        row = cur.fetchone()
        return float(row[0])
