# Gami Protocol MCP Stack

A full-stack deployment harness that stitches the autonomous agents in `../Gami_Agents` with the Horizon UI dashboard in `../gami-protocol-universal-engagement-layer`. It provisions PostgreSQL + Redis, exposes a FastAPI "brain" that proxies the Quest/Economy/Security agents, connects to Google Cloud Pub/Sub, and runs an MCP server **and** client side-by-side for AI-native control.

```
gami-protocol-mcp/
├── docker-compose.yml          # Orchestrates agents + infra + UI
├── run_simulation.py           # Load test / stress harness
├── .env                        # Environment variables (copy to .env.local for dev)
├── README.md                   # You are here
├── backend/                    # FastAPI + MCP bridge
│   ├── Dockerfile
│   ├── requirements.txt        # fastapi, uvicorn, redis, numpy, scikit-learn, google-cloud
│   ├── main.py                 # Supervisor / Router entrypoint
│   ├── agents/
│   │   ├── quest.py            # API & MCP wrappers
│   │   ├── economy.py
│   │   └── security.py
│   └── logic/
│       ├── quest_logic.py      # Cohort heuristics + SSE fan-out
│       ├── economy_logic.py    # Monte Carlo controller
│       └── security_logic.py   # Isolation Forest orchestration
└── frontend/                   # Horizon UI hook (proxied to ../gami-protocol-universal-engagement-layer)
```

## 1. Prerequisites

- Docker / Docker Compose v2+
- Python 3.11+ (for local tooling / `run_simulation.py`)
- Google Cloud service account JSON with Pub/Sub Publisher role (`PUBSUB_TOPIC`)
- Existing Gami agents built in `../Gami_Agents` (Quest/Economy/Security + MCP Supervisor)
- React dashboard inside `../gami-protocol-universal-engagement-layer`

## 2. Environment Variables

Copy `.env` to `.env.local` (or export in your shell) and update:

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_APPLICATION_CREDENTIALS` (mount path inside containers)
- `PUBSUB_TOPIC`
- `QUEST_AGENT_URL`, `ECONOMY_AGENT_URL`, `SECURITY_AGENT_URL` if you expose agents elsewhere
- `MCP_SERVER_PORT` if you need the backend MCP server on a different port (default 9300)

## 3. Docker Compose Workflow

```bash
cd gami-protocol-mcp
cp .env .env.local # edit values
docker compose --env-file .env.local up -d --build
```

Services spun up:

| Service | Description |
| --- | --- |
| `postgres` | Shared relational store for agents |
| `redis` | Hot state + SSE fan-out |
| `quest_agent`, `economy_agent`, `security_agent` | Built directly from `../Gami_Agents` Dockerfiles |
| `mcp_supervisor` | The existing MCP server from `../Gami_Agents/supervisor_agent` |
| `backend` | New FastAPI router + MCP bridge defined here |
| `frontend` | Horizon UI served from `../gami-protocol-universal-engagement-layer` |

The backend exposes:
- REST API at `http://localhost:9000/api/...`
- SSE stream at `/api/stream`
- MCP server at `http://localhost:9000/mcp` (SSE transport)

## 4. Google Cloud Connectivity

`backend/main.py` boots a Pub/Sub publisher and pushes every agent event + Monte Carlo result to `PUBSUB_TOPIC`. Provide credentials via Docker bind mount:

```bash
docker compose run backend \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/key.json \
  -v $HOME/.config/gcloud/service-account.json:/app/credentials/key.json:ro \
  uvicorn main:app
```

## 5. MCP Client + Server

- **Server:** `FastMCP` exposes tools `generate_quest`, `optimize_economy`, `check_fraud_risk`, and `push_dashboard_event` directly from the FastAPI logic.
- **Client:** A background `FastMCP` client connects to the supervisor running at `MCP_SUPERVISOR_URL` and mirrors tool definitions so other LLMs can prompt through a single surface.

## 6. Stress Testing

`run_simulation.py` spams mixed workloads (quest generation, economy sims, security checks) and validates Pub/Sub + SSE fan-out. Run it locally:

```bash
python run_simulation.py --users 25 --cycles 10
```

## 7. Frontend Wiring

`frontend/` acts as a design overlay (hooks + components) that mirrors the production Horizon UI stored in `../gami-protocol-universal-engagement-layer`. The Docker Compose target builds directly from that upstream folder, while these files document how to bind the SSE stream and widgets.

## 8. Development Tips

- Run `uvicorn backend.main:app --reload` for hot reload (requires installing `backend/requirements.txt`).
- Use `scripts/dev_proxy.sh` (coming soon) to forward SSE traffic when testing the Horizon UI separately.
- The MCP bridge logs to STDOUT; watch with `docker compose logs -f backend`.

---
Questions or contributions? Open an issue in this mono-repo and tag `@gami-core`.
