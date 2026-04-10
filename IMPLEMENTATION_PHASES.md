# Learnify Implementation Prioritization

This roadmap aligns with your selected stack:
- SQLAlchemy ORM using Declarative Base
- Alembic for schema migrations (recommended)
- Dockerization enabled
- React Context API for frontend state management

## Phase 1 - Foundation (Highest Priority)

1. Backend ORM baseline
- Add SQLAlchemy Declarative models for core tables.
- Centralize database URL as `SQLALCHEMY_DATABASE_URL`.
- Keep existing raw-query paths active to avoid regressions while migrating.

2. Migration workflow
- Add Alembic config and migration environment.
- Generate first migration from current models and validate on local DB.

3. Frontend state baseline
- Add global Context Provider for auth/session/theme/search state.
- Keep route/page contracts stable while shifting ownership from component state.

4. Docker local environment
- Add `docker-compose.yml` with MySQL, backend, and frontend services.
- Ensure local startup works with one command.

Definition of done:
- App runs via Docker Compose.
- Context Provider is active in frontend root.
- ORM/Alembic files exist and are runnable.

## Phase 2 - Migration and Hardening

1. Endpoint-by-endpoint ORM migration
- Replace cursor-based code in auth/history flows with SQLAlchemy Session queries.
- Add clear transaction boundaries and rollback handling.

2. Schema quality
- Add indexes/constraints through Alembic revisions.
- Add reversible migration scripts for all schema changes.

3. Operational hardening
- Add health checks for API and DB.
- Add structured logging and environment validation.

Definition of done:
- Core API paths use SQLAlchemy Session.
- Alembic history is the single source of truth for schema changes.
- Deployment setup can pass smoke tests in containers.

## Phase 3 - Scale and Reliability

1. Performance
- Optimize heavy queries and add pagination where missing.
- Add connection pool tuning based on load test results.

2. Test and CI maturity
- Add migration tests and API integration tests in CI.
- Validate Docker build and startup in pipeline.

3. Product reliability features
- Add cache strategy for expensive AI operations.
- Improve observability for task queues/background jobs.

Definition of done:
- Performance SLOs and error budgets tracked.
- CI enforces migrations, tests, and container checks.
- Production runbook updated for incident response.
