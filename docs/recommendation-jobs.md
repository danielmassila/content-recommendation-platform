# Recommendation job execution

User-triggered recomputation is scoped to the authenticated user. The Spring API starts the existing `reco-job`
container with `--user-id`; the Python job calculates one profile and replaces only that user's recommendation rows
inside the current database transaction.

Administrative recomputation remains a full batch operation. This distinction prevents a normal user action from
truncating and rebuilding recommendations for every account.

The synchronous process is bounded by `APP_RECOMMENDATIONS_JOB_TIMEOUT_SECONDS` (120 seconds by default). Timeout,
startup and worker failures are returned as HTTP 503 with code `RECOMMENDATION_JOB_UNAVAILABLE`.
`APP_RECOMMENDATIONS_COMPOSE_FILE` identifies the Compose file from the backend process working directory.

This remains a single-host portfolio deployment. The next scaling step is to replace process launching with a durable
queue and an independently deployed worker; the HTTP contract should then return `202 Accepted` and a job identifier.
