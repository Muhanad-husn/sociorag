# **SocioGraph Rebuild — Phase 8 Deep‑Dive Plan**

> **Objective:** Hard‑wire **quality gates and deployment utilities**: automated testing, static analysis, CI/CD on GitHub Actions, reproducible Docker images, and performance monitoring hooks — ensuring every subsequent commit ships safely to staging and prod.

---

## 🎯 Outcomes

| ID | Outcome | Acceptance Criteria |
|----|---------|---------------------|
| O‑8.1 | **100 %** of Python modules importable under `pytest -q` with **≥ 85 %** branch coverage. | Coverage XML check in CI |
| O‑8.2 | **Vitest** suite for UI passes & has **≥ 70 %** statements coverage. | `pnpm test` green |
| O‑8.3 | **Ruff**, **Black**, **isort**, and **mypy** all run in pre‑commit hook and CI; no warnings. | `pre-commit run --all-files` exits 0 |
| O‑8.4 | **GitHub Actions** pipeline executes jobs: _lint_ → _backend tests_ → _frontend tests_ → _docker build_; workflow finishes < 5 min. | `check.yml` passes on main |
| O‑8.5 | A **multi‑stage Dockerfile** builds a 250 MB compressed image serving FastAPI + static UI. | `docker images` size check |
| O‑8.6 | `docker compose up` starts API at `:8000` and UI at `:3000` reachable in browser. | Manual curl returns 200 |
| O‑8.7 | **Locust** load test reaches 50 RPS sustained with average latency < 200 ms on laptop. | Locust report |
| O‑8.8 | **Sentry** (self‑host or SaaS) captures unhandled exceptions client & server side. | Triggered error appears in Sentry dashboard. |

---

## 📋 CI/CD Pipeline Overview  fileciteturn5file6

```
on: [push, pull_request]
jobs:
  lint:
    ruff + mypy
  backend:
    matrix: {python: [3.12]}
    pytest --cov
  frontend:
    pnpm install; pnpm run test:unit
  docker:
    buildx build --push (main branch only)
  deploy:
    needs: docker
    environment: staging
    run: docker stack deploy ...
```

Secrets: `OPENROUTER_API_KEY`, `SENTRY_DSN`, `DOCKERHUB_TOKEN` injected via GitHub Actions secrets fileciteturn1file6.

---

## ⚙️ Prerequisites

* Docker ≥ 24, Compose v2 installed locally.
* GitHub repository with Actions enabled.
* `sentry-cli` if self‑hosting Sentry.

Install dev tools:

```bash
conda activate sociograph
pip install pytest-cov ruff mypy black isort locust
pnpm add -D vitest @testing-library/preact coverage
pre-commit install
```

---

## 🛠️ Step‑by‑Step Implementation

### 1  Static Analysis & Formatters

* **`pyproject.toml`**:

```toml
[tool.ruff]
line-length = 100
select = ["E","F","I","B"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.isort]
profile = "black"
```

* **`mypy.ini`** sets `strict = True`, excludes `ui/` bundle files.

### 2  Pytest & Coverage Enforcer

*Add `--cov=backend --cov-branch --cov-fail-under=85` to `pytest.ini`.*

Sample test for PDF generation speed using `pytest.mark.timeout(15)`.

### 3  Vitest & Coverage

`package.json`:

```json
"scripts": {
  "test": "vitest run --coverage",
  "test:watch": "vitest"
}
```

Configure `vitest.config.ts` to include `src/**/*.{ts,tsx}`.

### 4  GitHub Actions Workflows

**`.github/workflows/check.yml`**

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install ruff mypy black isort
      - run: ruff .
      - run: mypy backend

  backend:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r requirements.txt pytest pytest-cov
      - run: pytest --cov=backend --cov-report=xml

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm test

  docker:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USER }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - run: docker buildx build --push -t sociograph/backend:latest .
```

### 5  Dockerfile

```Dockerfile
# build stage
FROM python:3.12-slim AS builder
WORKDIR /app
COPY backend ./backend
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY backend ./backend
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Add separate `ui/Dockerfile` for nginx static serving; compose file binds them.

### 6  Docker Compose

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
    volumes:
      - ./vector_store:/app/vector_store
      - ./saved:/app/saved
  ui:
    build: ./ui
    ports: ["3000:80"]
    depends_on: [api]
```

### 7  Locust Load Test

`locustfile.py`:

```python
from locust import HttpUser, task, between
class SocioGraphUser(HttpUser):
    wait_time = between(1, 3)
    @task
    def ask(self):
        self.client.post("/search", json={"query": "What is RAG?"})
```

Run: `locust -u 100 -r 10 -t 1m`.

### 8  Sentry Integration

*Backend*: add middleware capturing exceptions:

```python
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))
```

*Frontend*: install `@sentry/browser`, init in `main.tsx`.

---

## 🕑 Estimated Effort

| Task | Time (hrs) |
|------|------------|
| Static analysis config | 1 |
| Test coverage tightening | 1.5 |
| GitHub Actions pipeline | 1 |
| Dockerfile & Compose | 1 |
| Load test script | 0.5 |
| Sentry hooks | 0.5 |
| **Total** | **~5.5 hrs** |

---

## 🚑 Troubleshooting & Tips

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Docker build > 1 GB | Poetry caches, pip cache | Add `--no-cache-dir` and `apt-get clean` |
| Locust spikes CPU > 80 % | Too many virtual users | Tune RPS, enable batching |
| Ruff reporting import‑order errors | isort order mismatch | Run `isort . && black .` |
| GitHub Actions exceeding 6 h monthly minutes | Heavy load tests on CI | Run Locust locally or schedule nightly cron jobs |

---

## 📝 Deliverables

1. **CI scripts** under `.github/workflows/`.  
2. **`pyproject.toml`** with formatter/linter configs.  
3. **Dockerfiles** and `docker-compose.yml`.  
4. **Locust** load‑testing script & README section.  
5. **Sentry** environment variables and docs.  
6. Git tag **`phase‑8`**.

---

_When GitHub Actions turn green, Docker compose spins up both services, and Locust hits 50 RPS < 200 ms, **Phase 8 is complete**. Final Phase 9 will tackle cloud deployment & observability dashboards._