"""Shared settings for global and per-user recommendation runs."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecommendationOptions:
    """Keep the same settings throughout a run; None selects application ratings only."""

    n_per_user: int = 20
    k_neighbors: int = 20
    algo_version: str = 'hybrid_usercf_pop'
    dataset_version: str | None = None
