# Performance budgets

Performance work is protected by explicit request and query budgets rather than relying only on subjective UI speed.

## Recommendation feed

Before sprint 5, loading 20 recommendations required:

- one request for recommendations;
- one request for ratings;
- up to 20 individual item requests.

The budget is now two frontend API requests regardless of the recommendation count. Each recommendation embeds its
normalized item representation. Spring Data uses an entity graph for `user` and `item`, keeping the repository page
query free of lazy-loading N+1 queries.

Run the frontend contract guard with:

```bash
make test-performance-contract
```

This is a structural budget. Production latency and database query counts should additionally be exported through
metrics once the application is deployed to a persistent environment.
