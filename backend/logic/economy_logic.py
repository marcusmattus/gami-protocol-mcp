"""Economy simulation orchestration."""
from __future__ import annotations

from typing import Any, Dict

import numpy as np


def local_monte_carlo(payload: Dict[str, Any]) -> Dict[str, Any]:
    current_supply = float(payload.get("current_supply", 1_000_000))
    adoption_rate = float(payload.get("adoption_rate", 5.0))
    days = int(payload.get("days", 30))
    iterations = int(payload.get("iterations", 500))

    inflations = []
    supply_paths = []
    for _ in range(iterations):
        supply = current_supply
        for _ in range(days):
            growth = np.random.normal(adoption_rate, adoption_rate * 0.25)
            growth = max(growth, 0)
            daily_emission = supply * 0.001 * (1 + growth / 100)
            supply += daily_emission
        supply_paths.append(supply)
        inflations.append((supply - current_supply) / current_supply * 100)

    return {
        "simulation_result": {
            "predicted_inflation": float(np.mean(inflations)),
            "inflation_std": float(np.std(inflations)),
            "mean_final_supply": float(np.mean(supply_paths)),
        },
        "adjustment_decision": {
            "trigger_deflationary_protocol": bool(np.mean(inflations) > 5.0),
        },
    }


async def run_economy_simulation(
    payload: Dict[str, Any],
    economy_agent: "EconomyAgent",
    telemetry: "TelemetryBus",
) -> Dict[str, Any]:
    try:
        result = await economy_agent.run_simulation(payload)
    except Exception:
        result = local_monte_carlo(payload)
    sim_block = result.get("simulation_result", {})
    decision_block = result.get("adjustment_decision", {})
    await telemetry.emit(
        event_type="economy.simulation",
        payload={
            "predicted_inflation": sim_block.get("predicted_inflation"),
            "trigger_deflation": decision_block.get("trigger_deflationary_protocol"),
        },
    )
    return result


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..agents.economy import EconomyAgent
    from ..telemetry import TelemetryBus
