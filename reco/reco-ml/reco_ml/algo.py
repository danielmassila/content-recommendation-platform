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
def compute_profile_maturity_threshold(ratings: List[Tuple[int, int, float]]) -> int:
    ratings_per_user: Dict[int, int] = {}

    for user_id, _, _ in ratings:
        ratings_per_user[user_id] = ratings_per_user.get(user_id, 0) + 1

    counts = list(ratings_per_user.values())

    if not counts:
        raise ValueError("No rating given")

    return int(statistics.median(counts))

def compute_alpha(n_ratings: int, profile_maturity_threshold: int, alpha_max: float = 0.9) -> float:
    k = max(1, int(profile_maturity_threshold))
    alpha = n_ratings / (n_ratings + k)
    if alpha_max is not None:
        alpha = min(alpha, alpha_max)
    return max(0.0, min(1.0, float(alpha)))

def mix_scores(cf_scores, pop_scores, alpha) -> dict[int, float]:
    mixed: Dict[int, float] = {}
    all_items = set(cf_scores.keys()) | set(pop_scores.keys())
    for item_id in all_items:
        cf_score = float(cf_scores.get(item_id, 0.0))
        pop_score = float(pop_scores.get(item_id, 0.0))
        mixed[item_id] = alpha * cf_score + (1.0 - alpha) * pop_score
    return mixed

def top_n(scores: Dict[int, float], n: int) -> List[tuple[int, float]]:
    if n <= 0 or not scores:
        return []
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:n]
def recommend_for_user(user_id: int, n: int, k: int, item_list: List[int], ratings_by_user: Dict[int, Dict[int, float]], users_by_item: Dict[int, Dict[int, float]], pop_scores_all: Dict[int, float], user_rating_count: Dict[int, int], profile_maturity_threshold: int):
    items_seen_by_user = ratings_by_user.get(user_id, {}).keys()
    items_to_discover = set(item_list) - set(items_seen_by_user)
    n_ratings = user_rating_count.get(user_id, 0)

    cf_scores: Dict[int, float] = {}
    pop_scores: Dict[int, float] = {}

    for i_id in items_to_discover:
        pop_scores[i_id] = pop_scores_all.get(i_id, 0.0)
        if n_ratings > 0:
            cf_scores[i_id] = score_cf(user_id, i_id, ratings_by_user, users_by_item, k)
        else:
            cf_scores[i_id] = 0.0

    alpha = compute_alpha(n_ratings, profile_maturity_threshold)
    cf_scores = normalize_scores(cf_scores)
    mixed_scores = mix_scores(cf_scores, pop_scores, alpha)

    return top_n(mixed_scores, n)

def recompute_all_recommendations(
    conn,
    n_per_user: int = 20,
    k_neighbors: int = 50,
    algo_version: str = "hybrid_usercf_pop",
) -> None:
    """
    Batch job:
    - fetch users/items/ratings + stats for popularity
    - build caches (ratings_by_user, users_by_item, user_rating_count)
    - compute profile_maturity_threshold once
    - compute popularity scores once
    - compute top-N recs for each user
    - write to recommendations table
    """
    # Fetch and compute data from database
    user_ids = repositories.fetch_all_users(conn)
    item_ids = repositories.fetch_all_items(conn)
    ratings = repositories.fetch_all_ratings(conn)
    stats_by_items = repositories.get_stats_by_item(conn)
    global_rating = repositories.get_global_rating(conn)

    # Build caches
    ratings_by_user = build_ratings_by_user(ratings)
    users_by_item = build_users_by_item(ratings)
    user_rating_count = {uid: len(ratings_by_user.get(uid, {})) for uid in user_ids}

    # Threshold and popularity
    profile_maturity_threshold = compute_profile_maturity_threshold(ratings)
    pop_scores_all = compute_popularity_from_stats(stats_by_items, global_rating)

    # Recommend for each user
    rows: List[RecommendationRow] = []

    for user_id in user_ids:
        recs = recommend_for_user(
            user_id=user_id,
            n=n_per_user,
            k=k_neighbors,
            item_list=item_ids,
            ratings_by_user=ratings_by_user,
            users_by_item=users_by_item,
            pop_scores_all=pop_scores_all,
            user_rating_count=user_rating_count,
            profile_maturity_threshold=profile_maturity_threshold,
        )

        # Convert to DB rows with ranks
        rank = 1
        for item_id, score in recs:
            rows.append(
                RecommendationRow(
                    user_id=int(user_id),
                    item_id=int(item_id),
                    score=float(score),
                    algo_version=algo_version,
                    rank=int(rank),
                )
            )
            rank += 1

    # Write into the database
    repositories.write_recommendations(conn, rows)
