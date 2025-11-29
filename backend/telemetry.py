"""Telemetry helpers: SSE broker + Redis + Pub/Sub fan-out."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Set

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SSEBroker:
    def __init__(self) -> None:
        self._clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def register(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._clients.add(queue)
        return queue

    async def unregister(self, queue: asyncio.Queue) -> None:
        async with self._lock:
            self._clients.discard(queue)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        async with self._lock:
            for queue in list(self._clients):
                await queue.put(payload)


class TelemetryBus:
    def __init__(
        self,
        sse_broker: SSEBroker,
        redis_client: Optional[redis.Redis],
        redis_channel: str,
        pubsub_publisher: Optional["PubSubPublisher"],
        pubsub_topic: Optional[str],
        origin: str = "backend-api",
    ) -> None:
        self.sse_broker = sse_broker
        self.redis_client = redis_client
        self.redis_channel = redis_channel
        self.pubsub_publisher = pubsub_publisher
        self.pubsub_topic = pubsub_topic
        self.origin = origin

    async def emit(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        envelope = {
            "event": event_type,
            "origin": self.origin,
            "payload": payload,
        }
        await self.sse_broker.broadcast(envelope)
        if self.redis_client is not None:
            try:
                await self.redis_client.publish(
                    self.redis_channel, json.dumps(envelope)
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Redis publish failed: %s", exc)
        if self.pubsub_publisher is not None and self.pubsub_topic:
            try:
                future = self.pubsub_publisher.publish(
                    self.pubsub_topic, json.dumps(envelope).encode("utf-8")
                )
                future.add_done_callback(lambda _: None)
            except Exception as exc:  # pragma: no cover
                logger.warning("Pub/Sub publish failed: %s", exc)
        return envelope


# Google Pub/Sub typing helper
try:  # pragma: no cover - optional dependency
    from google.cloud.pubsub_v1 import PublisherClient
except ImportError:  # pragma: no cover
    PublisherClient = None  # type: ignore

PubSubPublisher = PublisherClient
