"""Wrapper for the Security agent."""
from __future__ import annotations

from typing import Any, Dict

import httpx


class SecurityAgent:
    def __init__(
        self,
        base_url: str,
        http_client: httpx.AsyncClient,
        mcp_bridge: "MCPBridge" | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client
        self.mcp_bridge = mcp_bridge

    async def analyze_user(self, user_id: str) -> Dict[str, Any]:
        try:
            response = await self.http_client.post(
                f"{self.base_url}/detect-anomaly/{user_id}",
                json={},
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            if self.mcp_bridge:
                return await self._call_mcp(user_id)
            raise

    async def _call_mcp(self, user_id: str) -> Dict[str, Any]:
        if not self.mcp_bridge:
            raise RuntimeError("MCP bridge not configured")
        result = await self.mcp_bridge.call_tool(
            "check_fraud_risk", {"user_id": user_id}
        )
        if result and result.data:
            return result.data
        if result and result.structured_content:
            return result.structured_content
        return {"status": "fallback", "payload": result.content if result else {}}


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..mcp import MCPBridge
