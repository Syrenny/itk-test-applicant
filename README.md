# itk-test-applicant

[![Python](https://img.shields.io/badge/python-3.13-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-93%25-green)]()

> Simple wallet service for creating wallet operations (deposit/withdraw) and querying balances via REST API.

### Features

-   Create wallet operations (`DEPOSIT` / `WITHDRAW`) via REST
-   Query wallet balance
-   Concurrency-safe balance updates
-   PostgreSQL database with migrations
-   Full test coverage for API endpoints

### Tech Stack

-   **Backend:** FastAPI
-   **Database:** PostgreSQL
-   **Containerization:** Docker & docker-compose
-   **Python:** ≥3.13
-   **Testing:** Pytest & HTTPX (async tests) + Testcontainers for PG
-   **Migrations:** Alembic (applied automatically)

### Quick start

| Common Targets             | Purpose                              |
| -------------------------- | ------------------------------------ |
| `make up`                  | Build & start **PostgreSQL + app **  |
| `make down`                | Stop services & remove orphans       |
| `make ps`                  | List services in the full stack      |
| `make logs service=<name>` | Tail logs for the services           |
| `make up-infra`            | Start **infra only** (for local dev) |
| `make down-infra`          | Stop infra-only stack                |
| `make postgres-clean`      | **Remove** Postgres data volume      |

-   **Production-like (full stack: PostgreSQL + app)**
    ```bash
    make up                                     # build & start everything in detached mode
    make down                                   # stop and remove stack (keeps volumes)
    make ps                                     # show running containers
    make logs service=api-gateway               # tail logs for a service
    ```

*   **Development (infra only), run API/Web locally**

    ```bash
    make up-infra                               # start only PostgreSQL
    make ps-infra
    make logs-infra service=postgres            # tail a single infra service
    make down-infra
    ```

    > After `make up-infra`, run the **API** locally in dev mode (hot reload):
    >
    > ```bash
    > uv run -m src.main
    > ```

### Runnings tests

```bash
uv run -m pytest src/tests
```
