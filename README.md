# cryptopus-server

Server-side backend for **Cryptopus** — an RL-based algorithmic Bitcoin trading platform.

Part of the [AlgoTrading-Capstone](https://github.com/AlgoTrading-Capstone) organization.

---

## Overview

Cryptopus is a reinforcement learning meta-strategy that dynamically combines multiple trading
strategies to make Bitcoin trading decisions. This repository contains the cloud-deployed server
components that operate 24/7 and interface with the Kraken exchange.

The server is composed of three independent services deployed on AWS EKS:

| Service | Description |
|---|---|
| `api` | Django REST API + WebSocket server. Handles all client communication, authentication, and user operations. |
| `rl-inference` | Loads the trained RL agent from S3 and produces trading decisions (action/policy) on each market tick. |
| `trading-engine` | Executes trades on Kraken based on RL decisions. Manages positions, allocations, and persists trade history. |

---

## Repository Structure

```
cryptopus-server/
├── services/
│   ├── api/              # Django REST API + WebSocket (Daphne / Django Channels)
│   ├── rl-inference/     # RL inference engine (PyTorch)
│   └── trading-engine/   # Trade execution engine (APScheduler + CCXT)
├── shared/               # Shared Python package (state vector, normalization, constants)
├── infrastructure/       # Terraform — AWS infrastructure as code
├── helm/                 # Helm charts for Kubernetes deployment
└── .github/workflows/    # CI/CD pipelines per service
```

---

## Related Repositories

| Repository | Description |
|---|---|
| [cryptopus-client](https://github.com/AlgoTrading-Capstone/cryptopus-client) | Java desktop client (JavaFX) |
| [rl-training](https://github.com/AlgoTrading-Capstone/rl-training) | RL training and evaluation pipeline |
| [pinescript-converter](https://github.com/AlgoTrading-Capstone/pinescript-converter) | PineScript → Python strategy converter |
| [platform](https://github.com/AlgoTrading-Capstone/platform) | Project management and CI/CD coordination |

---

## Tech Stack

- **Python 3.11** · Django · Django REST Framework · Django Channels
- **PostgreSQL 16** + TimescaleDB · Redis (ElastiCache)
- **PyTorch** (RL inference) · CCXT (Kraken integration) · APScheduler
- **AWS**: EKS · RDS · ElastiCache · S3 · ECR · ALB · WAF · Secrets Manager
- **DevOps**: Docker · Kubernetes · Helm · ArgoCD · Terraform · GitHub Actions

---

## Getting Started

### Prerequisites

- Python 3.11.7
- Docker + Docker Compose
- TA-Lib C library (`apt install ta-lib` or `brew install ta-lib`)

### Run locally

```bash
git clone https://github.com/AlgoTrading-Capstone/cryptopus-server.git
cd cryptopus-server
docker compose up -d
```

The API runs migrations automatically on startup, so the database is ready once the containers are healthy.

### Run a specific service

```bash
cd services/api
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Rebuild after code changes

When you pull new code or change `Dockerfile` / `requirements.txt`:

```bash
docker compose up -d --build        # rebuild and restart
docker compose logs -f api          # follow api logs
```

To wipe the local database and start fresh (destroys all local data):

```bash
docker compose down -v
docker compose up -d --build
```

---

## Django Admin (manage users from the browser)

A superuser is **created automatically** the first time you run `docker compose up`. No manual commands needed.

Open the admin UI: **[http://localhost:8000/admin/](http://localhost:8000/admin/)**

| Field | Value |
|---|---|
| Email | `admin@cryptopus.local` |
| Password | `admin123` |

From there you can **add, edit, and delete users** (passwords are hashed automatically), manage groups/permissions, and inspect auth tables. To change the default credentials, edit the `DJANGO_SUPERUSER_*` env vars in `docker-compose.yml` before the first `up`.

### Managing the full login flow from admin

The **Users** page exposes every field the login pipeline cares about (`account_status`, `email_verified`, `otp_enabled`, `otp_secret`, `role`) and ships with bulk actions for the most common support workflows:

| Action | What it does |
|---|---|
| **Mark email as verified** | Flips `email_verified=True` so the user can log in without the emailed code |
| **Reset OTP** | Clears `otp_secret` + `otp_enabled` — user must re-pair their authenticator |
| **Activate account** / **Suspend account** | Toggles `account_status` between `ACTIVE` and `SUSPENDED` |
| **Force logout** | Blacklists all the user's JWT refresh tokens, invalidating active sessions |

Select one or more users in the list, pick an action from the **Action** dropdown, click **Go**. The JWT `Outstanding tokens` and `Blacklisted tokens` pages (under the **Token Blacklist** section) let you audit issued refresh tokens directly.

---

## Database Access (for frontend devs)

The Postgres container is exposed on the host for GUI clients (DataGrip, DBeaver, pgAdmin).

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `cryptopus` |
| User | `cryptopus` |
| Password | `cryptopus123` |

> Port `5433` is used to avoid conflicts with any native PostgreSQL install on `5432`.
> Inside the Docker network, services still reach Postgres at `postgres:5432`.

### DataGrip quick setup

1. **+** → **Data Source** → **PostgreSQL**.
2. Fill in the values from the table above.
3. If prompted, download the PostgreSQL driver.
4. **Test Connection** → **OK**.
5. In the data sources panel: right-click the connection → **Tools** → **Manage Shown Schemas** → check `public`.
6. Expand `cryptopus` → `public` → `tables` to browse the 19 tables (`users`, `trades`, `positions`, `candles`, etc.).

### Troubleshooting

- **`password authentication failed`** — a native Postgres is likely running on `5432`. Either stop it (`Stop-Service postgresql*` on Windows) or confirm you're connecting to port **5433**.
- **`public` schema is empty** — the API container hasn't run migrations yet. Check `docker compose ps` and `docker compose logs api`.
- **Connection refused** — containers aren't up. Run `docker compose up -d`.

---

## Environment Variables

Each service reads its configuration from environment variables (injected via AWS Secrets Manager
in production, `.env` file in development).

See `services/<service>/.env.example` for the required variables per service.

---
