"""Utilities for hosting and consuming MCP endpoints."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from fastmcp import Client, Context, FastMCP

logger = logging.getLogger(__name__)


class MCPBridge:
    def __init__(self, url: str | None) -> None:
        self.url = url
        self.client: Client | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if not self.url:
            return
        async with self._lock:
            if self.client is None:
                self.client = Client(self.url)
                await self.client.__aenter__()

    async def disconnect(self) -> None:
        async with self._lock:
            if self.client is not None:
                await self.client.__aexit__(None, None, None)
                self.client = None

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        if not self.url:
            raise RuntimeError("MCP supervisor URL not configured")
        await self.connect()
        assert self.client is not None  # for mypy
        return await self.client.call_tool(name=name, arguments=arguments)


def build_mcp_server(instructions: str) -> FastMCP:
    return FastMCP(
        name="gami_mcp_backend",
        instructions=instructions,
        version="1.0.0",
    )
