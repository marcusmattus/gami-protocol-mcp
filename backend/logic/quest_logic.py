"""Quest personalization heuristics + telemetry helpers."""
from __future__ import annotations

from typing import Any, Dict


def classify_cohort(reputation_score: float, xp_balance: int) -> str:
    if reputation_score < 20 or xp_balance < 250:
        return "rookie"
    if reputation_score < 60:
        return "core"
    return "elite"


async def generate_personalized_quest(
    user_profile: Dict[str, Any],
    quest_agent: "QuestAgent",
    telemetry: "TelemetryBus",
) -> Dict[str, Any]:
    cohort = classify_cohort(
        reputation_score=user_profile["user_identity"].get("reputation_score", 0),
        xp_balance=user_profile["user_identity"].get("xp_balance", 0),
    )
    quest = await quest_agent.generate_quest(user_profile)
    quest["cohort"] = cohort
    await telemetry.emit(
        event_type="quest.generated",
        payload={
            "cohort": cohort,
            "wallet_id": user_profile["user_identity"].get("wallet_id"),
            "quest_id": quest.get("quest_id"),
            "difficulty": quest.get("difficulty_rating"),
        },
    )
    return quest


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from ..agents.quest import QuestAgent
    from ..telemetry import TelemetryBus
