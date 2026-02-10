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
