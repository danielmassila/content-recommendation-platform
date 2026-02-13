# Content Recommendation Platform

This project is a backend-oriented content recommendation platform, designed to explore how recommendation systems can
be integrated into a real-world software architecture. For this first version, I decided to focus on movie
recommendation, but my initial goal was to mix the content recommendations, with books, songs and movies, so that I
solve a problem that I truly face: finding interesting new content to discover.

## Project Overview

Throughout this project, I wanted to explore how recommendation systems can be integrated into a real-world software
architecture.

This first version focuses on movie recommendations, but my initial goal was to mix the content recommendations, with
books, songs and movies, so that I solve a problem that I truly face: finding interesting new content to discover.

Rather than building a UI-centric application, I deliberately focused on:

- System design
- Data flow
- Architectural trade-offs
- Engineering constraints

I built the whole project based on an end-to-end recommendation pipeline:
data ingestion → storage → computation → API exposure.

## Architecture

The system is composed of:

- **Java (Spring Boot)** REST API
- **Python recommendation engine**
- **PostgreSQL** shared database
- **Docker Compose** for orchestration

The detailed architecture is available here:

👉 `docs/architecture.md`

---

## Recommendation Strategy

Hybrid model:

1. Bayesian-weighted popularity baseline
2. User-based collaborative filtering (using cosine similarity)
3. Dynamic hybrid blending based on profile maturity

Full explanation:
👉 `docs/recommendation.md`

---

## Quick Start

```bash
git clone <repo>
cd reco
make demo
```

Not done yet

- optimize the process of making recommendations (right now very long)
- add a doc about recommendation algorithm and one about performance evaluation
