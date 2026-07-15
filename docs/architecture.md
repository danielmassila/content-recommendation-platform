# Architecture Overview

This document describes both the macro-level system design and the internal backend layering decisions.

## 1 - Macro architecture

The system is composed of four main components:

- Spring Boot REST API (Java)
- Python Recommendation Engine
- PostgreSQL Database
- Docker Compose orchestration

These components interact as shown below:

- Java ↔ PostgreSQL via JPA
- Python ↔ PostgreSQL via psycopg
- Java triggers Python job through Docker process execution
- No direct REST communication in V1

This indirect coupling through the database was chosen deliberately for simplicity.

## 2 - Architectural philosophy

The primary goal of V1 is to build a **clean, understandable, evolvable system**, not to prematurely optimize
scalability.

### Known trade-offs

- The database acts as a coupling point.
- Recommendation computation is batch-oriented.
- There is no event-driven update mechanism.
- Recompute-all is not scalable for large datasets.

These limitations come from the simplicity of v1 and will be addressed in future versions.

## 3 - Backend Layered achitecture (Spring Boot)

The Java backend follows a classical layered architecture:

### Controller Layer

- Expose REST endpoints
- Validate input parameters
- Return DTO responses
- Handle HTTP concerns

### Service Layer

- Business logic
- Recommendation orchestration
- Transaction boundaries
- Triggering Python batch jobs

### Repository Layer

- Spring Data JPA
- Pagination support
- Custom query methods
- Database abstraction

## 4 - Python Recommendation Module

The Python side is structured to remain framework-independent.

Directory structure by responsibilities:

- Data fetching abstraction (`repositories.py`)
- Pure algorithm implementation (`algo.py`)
- Batch recomputation job (`run_reco.py`)
- Offline evaluation (`evaluate_offline.py`)
- Unit testing for pure functions

The recommendation logic is deliberately written as pure Python logic, decoupled from any web framework.

## 5 - Data flow

1. Dataset is downloaded.
2. Data is imported into PostgreSQL.
3. Python batch job:
    - fetches ratings
    - builds in-memory structures
    - computes recommendations
    - Writes results to `recommendations` table
4. Java API exposes recommendations via REST endpoints.

We clearly separate computation phase from serving phase.

## 6 - Infrastructure & deployment

All infrastructure aspects are managed through Docker Compose.

Services:

- db (PostgreSQL)
- adminer (DB UI)
- reco-job (Python container)
- Spring Boot app

Environment variables:

- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD

Flyway handles database migrations.

## 7 - Scalability perspectives

### What scales well

- Read-heavy serving (precomputed recommendations)
- Clear modular boundaries
- Containerized deployment

### What does not scale yet

- Full batch recomputation
- User-user similarity computed on the fly
- Database coupling between services
