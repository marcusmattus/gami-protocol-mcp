"""Wrapper for the Quest Generation agent (FastAPI microservice + MCP fallback)."""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class QuestAgent:
    def __init__(
        self,
        base_url: str,
        http_client: httpx.AsyncClient,
        mcp_bridge: "MCPBridge" | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client
        self.mcp_bridge = mcp_bridge

    async def generate_quest(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Quest microservice, falling back to MCP if needed."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/generate-quest",
                json=user_profile,
                timeout=45.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            if self.mcp_bridge:
                return await self._call_mcp(user_profile)
            raise

    async def _call_mcp(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp_bridge:
            raise RuntimeError("MCP bridge not configured")
        result = await self.mcp_bridge.call_tool(
            "generate_quest", {"user_profile": user_profile}
        )
        if result and result.data:
            return result.data
        if result and result.structured_content:
            return result.structured_content
        return {"status": "fallback", "payload": result.content if result else {}}


# Avoid circular imports (type checking only)
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..mcp import MCPBridge
