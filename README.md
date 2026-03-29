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
docker-compose up
```

### Run a specific service

```bash
cd services/api
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## Environment Variables

Each service reads its configuration from environment variables (injected via AWS Secrets Manager
in production, `.env` file in development).

See `services/<service>/.env.example` for the required variables per service.

---
