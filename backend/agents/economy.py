"""Wrapper for the Economy Management agent with MPC fallback."""
from __future__ import annotations

from typing import Any, Dict

import httpx


class EconomyAgent:
    def __init__(
        self,
        base_url: str,
        http_client: httpx.AsyncClient,
        mcp_bridge: "MCPBridge" | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client
        self.mcp_bridge = mcp_bridge

    async def run_simulation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = await self.http_client.post(
                f"{self.base_url}/run-simulation",
                json=payload,
                timeout=90.0,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            if self.mcp_bridge:
                return await self._call_mcp(payload)
            raise

    async def get_current_rate(self) -> Dict[str, Any]:
        response = await self.http_client.get(
            f"{self.base_url}/get-current-emission-rate", timeout=15.0
        )
        response.raise_for_status()
        return response.json()

    async def _call_mcp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp_bridge:
            raise RuntimeError("MCP bridge not configured")
        result = await self.mcp_bridge.call_tool(
            "optimize_economy", {"simulation": payload}
        )
        if result and result.data:
            return result.data
        if result and result.structured_content:
            return result.structured_content
        return {"status": "fallback", "payload": result.content if result else {}}


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..mcp import MCPBridge
