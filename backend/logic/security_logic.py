"""Security orchestration helpers."""
from __future__ import annotations

from typing import Dict


async def analyze_user(
    user_id: str,
    security_agent: "SecurityAgent",
    telemetry: "TelemetryBus",
) -> Dict:
    result = await security_agent.analyze_user(user_id)
    await telemetry.emit(
        event_type="security.alert",
        payload={
            "user_id": user_id,
            "is_anomaly": result.get("is_anomaly"),
            "anomaly_score": result.get("anomaly_score"),
            "action_taken": result.get("action_taken"),
        },
    )
    return result


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..agents.security import SecurityAgent
    from ..telemetry import TelemetryBus
