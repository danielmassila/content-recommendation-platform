import statistics
import math
import heapq
from typing import Dict, List, Tuple, Iterable
from reco_ml import repositories
from reco_ml.repositories import RecommendationRow
from collections import defaultdict

RatingRow = Tuple[int, int, float]

DEMO_CONFIG = {
    "pop_p": 300,
    "neighbor_pool": 30,
    "max_seed_items": 20,
    "max_raters_per_item": 30,
    "max_candidates_cf": 600,
    "k_neighbors": 20,
    "n_per_user": 20,
}


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


def top_n(scores: Dict[int, float], n: int) -> List[Tuple[int, float]]:
    if n <= 0 or not scores:
        return []
    return heapq.nlargest(n, scores.items(), key=lambda kv: kv[1])


def _pair_key(u: int, v: int) -> Tuple[int, int]:
    return (u, v) if u < v else (v, u)


def build_ratings_by_user(
    ratings: List[RatingRow],
) -> Dict[int, Dict[int, float]]:
    user_ratings: Dict[int, Dict[int, float]] = {}
    for user_id, item_id, rating in ratings:
        user_ratings.setdefault(user_id, {})[item_id] = float(rating)
    return user_ratings


def build_users_by_item(
    ratings: List[RatingRow],
) -> Dict[int, Dict[int, float]]:
    users_by_items: Dict[int, Dict[int, float]] = {}
    for user_id, item_id, rating in ratings:
        users_by_items.setdefault(item_id, {})[user_id] = float(rating)
    return users_by_items


def compute_popularity_from_stats(
    stats_by_items: Dict[int, Tuple[int, float]],
    global_rating: float,
    m: float | None = None,
    q: float = 0.80,
) -> Dict[int, float]:
    if not stats_by_items:
        return {}

    if m is None:
        counts = [v for (v, _) in stats_by_items.values()]
        m = choose_m(counts, quantile=q)

    m = float(m)

    pop_scores: Dict[int, float] = {}
    for item_id, (v, R) in stats_by_items.items():
        pop_scores[item_id] = (v / (v + m)) * R + (m / (v + m)) * global_rating

    return normalize_scores(pop_scores)


def top_p_items(pop_scores_all: Dict[int, float], p: int) -> List[int]:
    if p <= 0 or not pop_scores_all:
        return []
    return [
        item_id
        for item_id, _ in heapq.nlargest(
            p, pop_scores_all.items(), key=lambda kv: kv[1]
        )
    ]


def compute_user_cosine_similarity(
    user_u_id: int,
    user_v_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    sim_cache: Dict[Tuple[int, int], float],
) -> float:
    key = _pair_key(user_u_id, user_v_id)
    cached = sim_cache.get(key)
    if cached is not None:
        return cached

    ru = ratings_by_user.get(user_u_id, {})
    rv = ratings_by_user.get(user_v_id, {})

    if not ru or not rv:
        sim_cache[key] = 0.0
        return 0.0

    # iterate on smaller profile to reduce membership checks
    if len(ru) > len(rv):
        ru, rv = rv, ru

    num = 0.0
    den_u = 0.0
    den_v = 0.0

    for item_id, r_u in ru.items():
        r_v = rv.get(item_id)
        if r_v is None:
            continue
        num += r_u * r_v
        den_u += r_u * r_u
        den_v += r_v * r_v

    if den_u <= 0.0 or den_v <= 0.0:
        sim = 0.0
    else:
        sim = num / (math.sqrt(den_u) * math.sqrt(den_v))

    sim_cache[key] = float(sim)
    return float(sim)


def top_k_similar_users_for_item(
    user_id: int,
    item_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    k: int,
    sim_cache: Dict[Tuple[int, int], float],
    max_raters_per_item_cf: int = 200,
) -> List[Tuple[int, float, float]]:
    raters = users_by_item.get(item_id, {})
    if not raters:
        return []

    raters_sorted = heapq.nlargest(
        max_raters_per_item_cf, raters.items(), key=lambda kv: kv[1]
    )

    similar_users: List[Tuple[int, float, float]] = []
    for v_id, v_rating in raters_sorted:
        if v_id == user_id:
            continue
        sim = compute_user_cosine_similarity(user_id, v_id, ratings_by_user, sim_cache)
        if sim > 0.0:
            similar_users.append((v_id, sim, float(v_rating)))

    similar_users.sort(key=lambda t: t[1], reverse=True)
    return similar_users[:k] if k > 0 else similar_users


def score_cf(
    user_id: int,
    item_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    k: int,
    sim_cache: Dict[Tuple[int, int], float],
) -> float:
    if item_id in ratings_by_user.get(user_id, {}):
        return 0.0

    neighbors = top_k_similar_users_for_item(
        user_id, item_id, ratings_by_user, users_by_item, k, sim_cache
    )
    num = sum(sim * rating for _, sim, rating in neighbors)
    den = sum(sim for _, sim, _ in neighbors)

    return num / den if den > 0.0 else 0.0


def compute_profile_maturity_threshold(ratings: List[RatingRow]) -> int:
    ratings_per_user: Dict[int, int] = {}
    for user_id, _, _ in ratings:
        ratings_per_user[user_id] = ratings_per_user.get(user_id, 0) + 1

    if not ratings_per_user:
        raise ValueError("No ratings available")

    return int(statistics.median(ratings_per_user.values()))


def compute_bias_terms(
    ratings: List[RatingRow],
    reg_item: float = 10.0,
    reg_user: float = 15.0,
) -> tuple[float, Dict[int, float], Dict[int, float]]:
    """
    Baseline: r_ui ≈ mu + b_i + b_u

    reg_item/reg_user are shrinkage strengths:
    - higher => biases closer to 0 (more conservative)
    """
    if not ratings:
        return 0.0, {}, {}

    mu = sum(r for _, _, r in ratings) / len(ratings)

    # group ratings
    ratings_by_item: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
    ratings_by_user: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
    for u, i, r in ratings:
        ratings_by_item[i].append((u, float(r)))
        ratings_by_user[u].append((i, float(r)))

    # item bias: b_i = sum(r_ui - mu) / (reg_item + n_i)
    b_i: Dict[int, float] = {}
    for i, rows in ratings_by_item.items():
        s = sum((r - mu) for _, r in rows)
        b_i[i] = s / (reg_item + len(rows))

    # user bias: b_u = sum(r_ui - mu - b_i) / (reg_user + n_u)
    b_u: Dict[int, float] = {}
    for u, rows in ratings_by_user.items():
        s = 0.0
        for i, r in rows:
            s += r - mu - b_i.get(i, 0.0)
        b_u[u] = s / (reg_user + len(rows))

    return float(mu), b_i, b_u


def score_cf_with_bias(
    user_id: int,
    item_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    k: int,
    sim_cache: Dict[Tuple[int, int], float],
    mu: float,
    b_i: Dict[int, float],
    b_u: Dict[int, float],
) -> float:
    """
    Predict rating using neighborhood CF on residuals:
    pred = baseline(u,i) + weighted_avg( residual(v,i) )
    where residual(v,i) = r_vi - baseline(v,i)
    """
    if item_id in ratings_by_user.get(user_id, {}):
        return 0.0

    neighbors = top_k_similar_users_for_item(
        user_id, item_id, ratings_by_user, users_by_item, k, sim_cache
    )
    if not neighbors:
        # fallback: baseline only
        return float(mu + b_u.get(user_id, 0.0) + b_i.get(item_id, 0.0))

    num = 0.0
    den = 0.0
    for v_id, sim, r_vi in neighbors:
        baseline_vi = mu + b_u.get(v_id, 0.0) + b_i.get(item_id, 0.0)
        resid = float(r_vi) - float(baseline_vi)
        num += float(sim) * resid
        den += float(sim)

    baseline_ui = mu + b_u.get(user_id, 0.0) + b_i.get(item_id, 0.0)
    adj = (num / den) if den > 0.0 else 0.0
    return float(baseline_ui + adj)


def compute_alpha(
    n_ratings: int,
    profile_maturity_threshold: int,
    alpha_max: float = 0.9,
) -> float:
    k = max(1, profile_maturity_threshold)
    alpha = n_ratings / (n_ratings + k)
    return min(alpha, alpha_max)


def mix_scores(
    cf_scores: Dict[int, float],
    pop_scores: Dict[int, float],
    alpha: float,
) -> Dict[int, float]:
    items = set(cf_scores.keys()) | set(pop_scores.keys())
    return {
        item_id: alpha * cf_scores.get(item_id, 0.0)
        + (1.0 - alpha) * pop_scores.get(item_id, 0.0)
        for item_id in items
    }


def build_candidates_for_user(
    user_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    all_items_set: set[int],
    pop_top_items: List[int],
    sim_cache: Dict[Tuple[int, int], float],
    neighbor_pool: int = DEMO_CONFIG["neighbor_pool"],
    max_seed_items: int = DEMO_CONFIG["max_seed_items"],
    max_raters_per_item: int = DEMO_CONFIG["max_raters_per_item"],
    rating_threshold: float = 4.0,
    max_candidates_cf: int = DEMO_CONFIG["max_candidates_cf"],
) -> set[int]:
    seen = ratings_by_user.get(user_id, {})
    seen_set = set(seen.keys())

    if not seen_set:
        return set(pop_top_items)

    candidates: set[int] = set(pop_top_items)

    seed_items = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
    seed_items = [item_id for item_id, _ in seed_items[:max_seed_items]]

    neighbor_scores: Dict[int, float] = {}

    for item_id in seed_items:
        raters = users_by_item.get(item_id, {})
        if not raters:
            continue

        raters_sorted = heapq.nlargest(
            max_raters_per_item, raters.items(), key=lambda kv: kv[1]
        )

        for v_id, _ in raters_sorted:
            if v_id == user_id:
                continue
            sim = compute_user_cosine_similarity(
                user_id, v_id, ratings_by_user, sim_cache
            )
            if sim > neighbor_scores.get(v_id, 0.0):
                neighbor_scores[v_id] = sim

    if not neighbor_scores:
        return (candidates & all_items_set) - seen_set

    top_neighbors = sorted(neighbor_scores.items(), key=lambda kv: kv[1], reverse=True)[
        :neighbor_pool
    ]

    cf_candidates: set[int] = set()
    for v_id, _ in top_neighbors:
        for item_id, r in ratings_by_user.get(v_id, {}).items():
            if item_id not in seen_set and r >= rating_threshold:
                cf_candidates.add(item_id)
                if len(cf_candidates) >= max_candidates_cf:
                    break
        if len(cf_candidates) >= max_candidates_cf:
            break

    return (candidates | cf_candidates) & all_items_set - seen_set


def build_neighbor_pool_for_user(
    user_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    sim_cache: Dict[Tuple[int, int], float],
    neighbor_pool: int = DEMO_CONFIG["neighbor_pool"],
    max_seed_items: int = DEMO_CONFIG["max_seed_items"],
    max_raters_per_item: int = DEMO_CONFIG["max_raters_per_item"],
) -> List[Tuple[int, float]]:
    seen = ratings_by_user.get(user_id, {})
    if not seen:
        return []

    seed_items = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
    seed_items = [item_id for item_id, _ in seed_items[:max_seed_items]]

    neighbor_scores: Dict[int, float] = {}

    for item_id in seed_items:
        raters = users_by_item.get(item_id, {})
        if not raters:
            continue

        raters_top = heapq.nlargest(
            max_raters_per_item, raters.items(), key=lambda kv: kv[1]
        )

        for v_id, _ in raters_top:
            if v_id == user_id:
                continue
            sim = compute_user_cosine_similarity(
                user_id, v_id, ratings_by_user, sim_cache
            )
            if sim > neighbor_scores.get(v_id, 0.0):
                neighbor_scores[v_id] = sim

    if not neighbor_scores:
        return []

    return heapq.nlargest(neighbor_pool, neighbor_scores.items(), key=lambda kv: kv[1])


def score_cf_with_bias_from_pool(
    user_id: int,
    item_id: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    neighbor_pool: List[Tuple[int, float]],  # [(v_id, sim)]
    mu: float,
    b_i: Dict[int, float],
    b_u: Dict[int, float],
) -> float:
    # already rated => do not recommend
    if item_id in ratings_by_user.get(user_id, {}):
        return 0.0

    baseline_ui = mu + b_u.get(user_id, 0.0) + b_i.get(item_id, 0.0)

    num = 0.0
    den = 0.0

    for v_id, sim in neighbor_pool:
        r_vi = ratings_by_user.get(v_id, {}).get(item_id)
        if r_vi is None:
            continue

        baseline_vi = mu + b_u.get(v_id, 0.0) + b_i.get(item_id, 0.0)
        resid = float(r_vi) - float(baseline_vi)

        num += float(sim) * resid
        den += float(sim)

    if den <= 0.0:
        return float(baseline_ui)

    return float(baseline_ui + (num / den))


def recommend_for_user(
    user_id: int,
    n: int,
    k: int,
    ratings_by_user: Dict[int, Dict[int, float]],
    users_by_item: Dict[int, Dict[int, float]],
    pop_scores_all: Dict[int, float],
    user_rating_count: Dict[int, int],
    profile_maturity_threshold: int,
    all_items_set: set[int],
    pop_top_items: List[int],
    mu: float,
    b_i: Dict[int, float],
    b_u: Dict[int, float],
) -> List[Tuple[int, float]]:
    sim_cache: Dict[Tuple[int, int], float] = {}

    candidates = build_candidates_for_user(
        user_id=user_id,
        ratings_by_user=ratings_by_user,
        users_by_item=users_by_item,
        all_items_set=all_items_set,
        pop_top_items=pop_top_items,
        sim_cache=sim_cache,
    )

    neighbor_pool_list = build_neighbor_pool_for_user(
        user_id=user_id,
        ratings_by_user=ratings_by_user,
        users_by_item=users_by_item,
        sim_cache=sim_cache,
        neighbor_pool=DEMO_CONFIG["neighbor_pool"],
        max_seed_items=DEMO_CONFIG["max_seed_items"],
        max_raters_per_item=DEMO_CONFIG["max_raters_per_item"],
    )

    n_ratings = user_rating_count.get(user_id, 0)
    alpha = compute_alpha(n_ratings, profile_maturity_threshold)

    cf_scores: Dict[int, float] = {}
    pop_scores: Dict[int, float] = {}

    for item_id in candidates:
        pop_scores[item_id] = pop_scores_all.get(item_id, 0.0)
        cf_scores[item_id] = (
            score_cf_with_bias_from_pool(
                user_id=user_id,
                item_id=item_id,
                ratings_by_user=ratings_by_user,
                neighbor_pool=neighbor_pool_list,
                mu=mu,
                b_i=b_i,
                b_u=b_u,
            )
            if n_ratings > 0
            else float(mu + b_u.get(user_id, 0.0) + b_i.get(item_id, 0.0))
        )
        # WE CHANGED THE CF FUNCTION ADDING THE BIAS

    cf_scores = normalize_scores(cf_scores)
    mixed_scores = {
        item_id: alpha * cf_scores[item_id] + (1.0 - alpha) * pop_scores[item_id]
        for item_id in candidates
    }
    return top_n(mixed_scores, n)

def recompute_all_recommendations(
    conn,
    n_per_user: int = DEMO_CONFIG["n_per_user"],
    k_neighbors: int = DEMO_CONFIG["k_neighbors"],
    algo_version: str = "hybrid_usercf_pop",
) -> None:
    user_ids = repositories.fetch_all_users(conn)
    item_ids = repositories.fetch_all_items(conn)
    all_items_set = set(item_ids)

    ratings = repositories.fetch_all_ratings(conn)
    stats_by_items = repositories.get_stats_by_item(conn)
    global_rating = repositories.get_global_rating(conn)

    ratings_by_user = build_ratings_by_user(ratings)
    users_by_item = build_users_by_item(ratings)
    user_rating_count = {u: len(ratings_by_user.get(u, {})) for u in user_ids}

    # Threshold and popularity
    profile_threshold = compute_profile_maturity_threshold(ratings)
    pop_scores_all = compute_popularity_from_stats(stats_by_items, global_rating)
    pop_top_items = top_p_items(pop_scores_all, p=DEMO_CONFIG["pop_p"])

    # Bias terms
    mu, b_i, b_u = compute_bias_terms(ratings, reg_item=10.0, reg_user=15.0)

    # Recommend for each user
    rows: List[RecommendationRow] = []

    for user_id in user_ids:
        recs = recommend_for_user(
            user_id=user_id,
            n=n_per_user,
            k=k_neighbors,
            ratings_by_user=ratings_by_user,
            users_by_item=users_by_item,
            pop_scores_all=pop_scores_all,
            user_rating_count=user_rating_count,
            profile_maturity_threshold=profile_threshold,
            all_items_set=all_items_set,
            pop_top_items=pop_top_items,
            mu=mu,
            b_i=b_i,
            b_u=b_u,
        )

        for rank, (item_id, score) in enumerate(recs, start=1):
            rows.append(
                RecommendationRow(
                    user_id=int(user_id),
                    item_id=int(item_id),
                    score=float(score),
                    algo_version=algo_version,
                    rank=rank,
                )
            )

    repositories.write_recommendations(conn, rows)
