# Security model

## Authorization

- New accounts receive the `USER` role.
- Administrative operations require `ROLE_ADMIN` in the Spring Security filter chain.
- Personal resources are exposed below `/api/v1/me`; the backend derives the user id
  from the authenticated principal and never accepts it from the request body.
- Legacy routes below `/api/v1/users/**` and `/api/v1/ratings/**` are restricted to
  administrators while clients migrate to the current-user API.
- Movie catalogue reads remain public. Catalogue writes require an administrator.

## Authentication failures

Authentication and authorization failures use `application/problem+json`:

- `401 AUTHENTICATION_REQUIRED` for a missing or invalid session;
- `401 INVALID_CREDENTIALS` for a failed login;
- `403 ACCESS_DENIED` for insufficient privileges;
- `429 RATE_LIMIT_EXCEEDED` when an abuse-protection threshold is exceeded.

## Rate limiting

Login, registration and recommendation recomputation are protected by a bounded,
per-instance fixed-window limiter. It deliberately uses the servlet remote address and
does not trust forwarding headers by default. A multi-replica deployment must replace
or complement it with a shared limiter at the trusted ingress/API gateway.

## Production configuration

The `prod` Spring profile requires an explicit JWT secret and explicit CORS origins.
Secrets must never be committed or delivered to the browser.
