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
- React product interface

The focus is on clarity and system foundations.

## V2 — Targeted recommendation updates

- Per-user recomputation (implemented)
- Bounded recommendation jobs (implemented)
- Similarity Precomputation
- Caching layer
- Performance and testing improvements

## V3 — From database coupling to microservices

**Dedicated Recommender microservice**

- Python microservice with REST API
- Explicit communication contract
- Remove the whole database coupling

## V4 — Product-level platform

- Event-driven pipeline
- ML-based models for better recommendations
    - Matrix factorization
    - Neural collaborative filtering
    - Embedding-based similarity
- Observability
    - Logging
    - Monitoring
    - Performance dashboards
