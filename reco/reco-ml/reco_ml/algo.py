import statistics
import math
from typing import Dict, List, Tuple, Iterable
from reco_ml import repositories
from reco_ml.repositories import RecommendationRow


def choose_m(counts: Iterable[int], quantile: float = 0.80) -> float:
    counts = sorted(counts)

    if not counts:
        raise ValueError("counts must not be empty")

    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be between 0 and 1")

    index = math.ceil(quantile * len(counts)) - 1
    index = max(0, min(index, len(counts) - 1))

    return float(counts[index])


def normalize_scores(scores: Dict[int, float]) -> Dict[int, float]:

    if not scores:
        return {}

    values = scores.values()
    min_score = min(values)
    max_score = max(values)

    if max_score == min_score:
        return {item_id: 0.0 for item_id in scores}

    return {
        item_id: (score - min_score) / (max_score - min_score)
        for item_id, score in scores.items()
    }

def compute_popularity_from_stats(stats_by_items: Dict[int, tuple[int, float]], global_rating: float, m=None, q=0.80) -> Dict[int, float]:
    if not stats_by_items:
        return {}

    if not 0.0 < q < 1.0:
        raise ValueError("q must be between 0 and 1")

    if m is None: # we choose m from data only if not given
        counts = [v for (v, _) in stats_by_items.values()]
        m = choose_m(counts, quantile=q)

    m = float(m)

    popularity_scores: Dict[int, float] = {}
    for item_id, (v, R) in stats_by_items.items():
        popularity_scores[item_id] = (v / (v + m))*R + (m/(v + m))*global_rating
    return normalize_scores(popularity_scores)

def ranked_items(scores: Dict[int, float]) -> list[tuple[int, float]]:
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
def build_ratings_by_user(ratings: List[Tuple[int, int, float]]) -> Dict[int, Dict[int, float]]:
    user_ratings: Dict[int, Dict[int, float]] = {}
    for user_id, item_id, rating in ratings:
        if user_id not in user_ratings:
            user_ratings[user_id] = {}
        user_ratings[user_id][item_id] = float(rating)
    return user_ratings


def build_users_by_item(ratings: List[Tuple[int, int, float]]) -> Dict[int, Dict[int, float]]:
    users_by_items: Dict[int, Dict[int, float]] = {}
    for user_id, item_id, rating in ratings:
        if item_id not in users_by_items:
            users_by_items[item_id] = {}
        users_by_items[item_id][user_id] = float(rating)
    return users_by_items
def compute_user_cosine_similarity(user_u_id: int, user_v_id: int, ratings_by_user: Dict[int, Dict[int, float]]) -> float:
    ratings_u = ratings_by_user.get(user_u_id, {})
    ratings_v = ratings_by_user.get(user_v_id, {})
    movies_seen_by_both = set(ratings_u.keys()) & set(ratings_v.keys())

    if not ratings_u or not ratings_v or not movies_seen_by_both:
        return 0.0

    num = sum(ratings_u[mv] * ratings_v[mv] for mv in movies_seen_by_both)
    den_u = math.sqrt(sum(ratings_u[mv] ** 2 for mv in movies_seen_by_both))
    den_v = math.sqrt(sum(ratings_v[mv] ** 2 for mv in movies_seen_by_both))
    den = den_u * den_v

    if den == 0.0:
        return 0.0

    return num / den

def score_cf(user_id: int, item_id: int, ratings_by_user: Dict[int, Dict[int, float]], users_by_item: Dict[int, Dict[int, float]], k: int) -> float:
    if item_id in ratings_by_user.get(user_id, {}):
        return 0.0
    similar_users = top_k_similar_users_for_item(user_id, item_id, ratings_by_user, users_by_item, k)
    num = sum(sim[1] * sim[2] for sim in similar_users)
    den = sum(sim[1] for sim in similar_users)
    if den == 0.0:
        return 0.0
    return num / den

def top_k_similar_users_for_item(user_id: int,
    item_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    k: int
    ) -> List[Tuple[int, float, float]]:

    raters = users_by_item.get(item_id, {})
    if not raters:
        return []

    similar_users: List[Tuple[int, float, float]] = []
    for v_id, v_rating_on_item in raters.items():
        if v_id == user_id:
            continue
        sim = compute_user_cosine_similarity(user_id, v_id, ratings_by_user)
        if sim > 0.0:
            similar_users.append((v_id, sim, float(v_rating_on_item)))

    similar_users.sort(key=lambda t: t[1], reverse=True)
    if k > 0:
        similar_users = similar_users[:k]
    return similar_users
