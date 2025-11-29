"""FastAPI + MCP bridge for the Gami Protocol MCP stack."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from asyncio import Task
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from agents.economy import EconomyAgent
from agents.quest import QuestAgent
from agents.security import SecurityAgent
from logic import economy_logic, quest_logic, security_logic
from mcp import MCPBridge, build_mcp_server
from telemetry import SSEBroker, TelemetryBus, PubSubPublisher
from fastmcp import Context

# Load .env if present for local dev
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)

logger = logging.getLogger("gami.mcp.backend")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


@dataclass
class Settings:
    quest_agent_url: str = os.getenv("QUEST_AGENT_URL", "http://localhost:8001")
    economy_agent_url: str = os.getenv("ECONOMY_AGENT_URL", "http://localhost:8002")
    security_agent_url: str = os.getenv("SECURITY_AGENT_URL", "http://localhost:8003")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_channel: str = os.getenv("SSE_CHANNEL", "agent-events")
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "9000"))
    mcp_server_port: int = int(os.getenv("MCP_SERVER_PORT", "9300"))
    mcp_server_path: str = os.getenv("MCP_SERVER_PATH", "mcp")
    mcp_supervisor_url: str | None = os.getenv("MCP_SUPERVISOR_URL")
    google_credentials: str | None = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    google_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    pubsub_topic: str | None = os.getenv("PUBSUB_TOPIC")


settings = Settings()

# Globals initialised during lifespan
http_client: httpx.AsyncClient | None = None
redis_client: redis.Redis | None = None
telemetry_bus: TelemetryBus | None = None
pubsub_publisher: PubSubPublisher | None = None
pubsub_topic_path: str | None = None
mcp_bridge = MCPBridge(settings.mcp_supervisor_url)

quest_agent_client: QuestAgent | None = None
economy_agent_client: EconomyAgent | None = None
security_agent_client: SecurityAgent | None = None

sse_broker = SSEBroker()
background_tasks: List[Task] = []

MCP_INSTRUCTIONS = """You expose Gami Protocol quest, economy, and security controls as MCP tools.
Honor the canonical schemas (UserIdentity, Quest, MCPEvent) and never invent new fields.
"""

mcp_server = build_mcp_server(MCP_INSTRUCTIONS)


# --------------------------- Pydantic Schemas ---------------------------------


class QuestPayload(BaseModel):
    user_identity: Dict[str, Any]
    recent_events: List[Dict[str, Any]] = Field(default_factory=list)
    total_quests_completed: int = 0
    average_completion_time: float = 0.0


class EconomySimulationPayload(BaseModel):
    current_supply: float = Field(..., gt=0)
    adoption_rate: float = Field(..., ge=0, le=100)
    days: int = Field(default=30, ge=1, le=365)
    iterations: int = Field(default=1000, ge=100, le=10000)


class SecurityPayload(BaseModel):
    user_id: str


# --------------------------- Dependency Helpers -------------------------------


def require_telemetry() -> TelemetryBus:
    if telemetry_bus is None:
        raise RuntimeError("Telemetry bus not initialised")
    return telemetry_bus


def require_quest_agent() -> QuestAgent:
    if quest_agent_client is None:
        raise RuntimeError("Quest agent not ready")
    return quest_agent_client


def require_economy_agent() -> EconomyAgent:
    if economy_agent_client is None:
        raise RuntimeError("Economy agent not ready")
    return economy_agent_client


def require_security_agent() -> SecurityAgent:
    if security_agent_client is None:
        raise RuntimeError("Security agent not ready")
    return security_agent_client


# --------------------------- SSE Handling -------------------------------------


async def stream_events() -> EventSourceResponse:
    queue = await sse_broker.register()

    async def event_generator() -> AsyncGenerator[Dict[str, Any], None]:
        try:
            while True:
                event = await queue.get()
                yield {"event": event.get("event", "message"), "data": json.dumps(event)}
        finally:
            await sse_broker.unregister(queue)

    return EventSourceResponse(event_generator(), ping=10)


async def redis_listener() -> None:
    if redis_client is None:
        return
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(settings.redis_channel)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            raw_data = message.get("data")
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8")
            try:
                payload = json.loads(raw_data)
            except Exception:  # pragma: no cover
                continue
            if payload.get("origin") == "backend-api":
                continue
            await sse_broker.broadcast(payload)
    finally:
        await pubsub.close()


# --------------------------- MCP Tool bindings --------------------------------


@mcp_server.tool(name="generate_quest", description="Generate quest via FastAPI supervisor")
async def mcp_generate_quest_tool(
    user_profile: Dict[str, Any], context: Context | None = None
) -> Dict[str, Any]:
    telemetry = require_telemetry()
    quest_agent = require_quest_agent()
    return await quest_logic.generate_personalized_quest(user_profile, quest_agent, telemetry)


@mcp_server.tool(name="optimize_economy", description="Run Monte Carlo simulation")
async def mcp_optimize_economy_tool(
    simulation: Dict[str, Any], context: Context | None = None
) -> Dict[str, Any]:
    telemetry = require_telemetry()
    economy_agent = require_economy_agent()
    return await economy_logic.run_economy_simulation(simulation, economy_agent, telemetry)


@mcp_server.tool(name="check_fraud_risk", description="Check for anomalies via security agent")
async def mcp_check_fraud_tool(
    user_id: str, context: Context | None = None
) -> Dict[str, Any]:
    telemetry = require_telemetry()
    security_agent = require_security_agent()
    return await security_logic.analyze_user(user_id, security_agent, telemetry)


async def run_mcp_server_task() -> None:
    await mcp_server.run_async(
        transport="sse",
        host=settings.backend_host,
        port=settings.mcp_server_port,
        path=settings.mcp_server_path,
        show_banner=False,
    )


# --------------------------- FastAPI App --------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, redis_client, telemetry_bus, pubsub_publisher, pubsub_topic_path
    global quest_agent_client, economy_agent_client, security_agent_client

    http_client = httpx.AsyncClient()
    redis_client = redis.from_url(settings.redis_url, decode_responses=False)

    pubsub_topic_path = None
    if (
        settings.google_project
        and settings.pubsub_topic
        and PubSubPublisher is not None
    ):
        try:
            pubsub_publisher = PubSubPublisher()
            if settings.pubsub_topic.startswith("projects/"):
                pubsub_topic_path = settings.pubsub_topic
            else:
                pubsub_topic_path = (
                    f"projects/{settings.google_project}/topics/{settings.pubsub_topic}"
                )
        except Exception as exc:  # pragma: no cover
            logger.warning("Pub/Sub initialisation failed: %s", exc)
            pubsub_publisher = None
    else:
        pubsub_publisher = None

    telemetry_bus = TelemetryBus(
        sse_broker=sse_broker,
        redis_client=redis_client,
        redis_channel=settings.redis_channel,
        pubsub_publisher=pubsub_publisher,
        pubsub_topic=pubsub_topic_path,
    )

    quest_agent_client = QuestAgent(settings.quest_agent_url, http_client, mcp_bridge)
    economy_agent_client = EconomyAgent(settings.economy_agent_url, http_client, mcp_bridge)
    security_agent_client = SecurityAgent(settings.security_agent_url, http_client, mcp_bridge)

    # background tasks
    redis_task = asyncio.create_task(redis_listener())
    mcp_server_task = asyncio.create_task(run_mcp_server_task())
    await mcp_bridge.connect()

    background_tasks.extend([redis_task, mcp_server_task])

    try:
        yield
    finally:
        for task in background_tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        background_tasks.clear()

        if http_client is not None:
            await http_client.aclose()
            http_client = None

        if redis_client is not None:
            await redis_client.close()
            redis_client = None

        if pubsub_publisher is not None:
            pubsub_publisher.close()
            pubsub_publisher = None

        quest_agent_client = None
        economy_agent_client = None
        security_agent_client = None
        telemetry_bus = None

        await mcp_bridge.disconnect()


app = FastAPI(
    title="Gami Protocol MCP Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "agents": {
            "quest": quest_agent_client is not None,
            "economy": economy_agent_client is not None,
            "security": security_agent_client is not None,
        },
        "mcp_server_port": settings.mcp_server_port,
    }


@app.get("/api/stream")
async def sse_endpoint() -> EventSourceResponse:
    return await stream_events()


@app.post("/api/quests/generate")
async def api_generate_quest(
    payload: QuestPayload,
    quest_agent: QuestAgent = Depends(require_quest_agent),
    telemetry: TelemetryBus = Depends(require_telemetry),
) -> Dict[str, Any]:
    return await quest_logic.generate_personalized_quest(payload.model_dump(), quest_agent, telemetry)


@app.post("/api/economy/simulate")
async def api_run_simulation(
    payload: EconomySimulationPayload,
    economy_agent: EconomyAgent = Depends(require_economy_agent),
    telemetry: TelemetryBus = Depends(require_telemetry),
) -> Dict[str, Any]:
    return await economy_logic.run_economy_simulation(payload.model_dump(), economy_agent, telemetry)


@app.get("/api/economy/rate")
async def api_get_rate(
    economy_agent: EconomyAgent = Depends(require_economy_agent),
) -> Dict[str, Any]:
    return await economy_agent.get_current_rate()


@app.post("/api/security/analyze")
async def api_security_analyze(
    payload: SecurityPayload,
    security_agent: SecurityAgent = Depends(require_security_agent),
    telemetry: TelemetryBus = Depends(require_telemetry),
) -> Dict[str, Any]:
    return await security_logic.analyze_user(payload.user_id, security_agent, telemetry)
