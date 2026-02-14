# Roadmap

This project follows an incremental evolution philosophy, so that I can keep on working on it with at the same time a
functional version. I follow a particular (and ambitious) long-term vision : transforming that system from an
educational hybrid recommender into a production-grade modular recommendation platform.

## V1 — Hybrid batch recommender

- Popularity + UserCF
- Batch computation
- Database communication
- Offline evaluation
- Dockerized environment

The focus is on clarity and system foundations.

## V2 — System engineering upgrades

- Per-user recomputation
- Avoid full-batch recompute
- Similarity Precomputation
- Caching layer
- Performance and testing improvements

## V3 — From database coupling to microservices

**Dedicated Recommender microservice**

- Python microservice with REST API
- Explicit communication contract
- Remove the whole database coupling

## V4 — Product-level platform

- Frontend
- Event-driven pipeline
- ML-based models for better recommendations
    - Matrix factorization
    - Neural collaborative filtering
    - Embedding-based similarity
- Observability
    - Logging
    - Monitoring
    - Performance dashboards
