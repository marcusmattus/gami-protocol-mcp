"""Stress test harness for the Gami Protocol MCP stack."""
from __future__ import annotations

import asyncio
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import httpx

API_BASE = os.getenv("API_BASE", "http://localhost:9000/api")
USERS = int(os.getenv("SIM_USERS", "10"))
CYCLES = int(os.getenv("SIM_CYCLES", "5"))


@dataclass
class User:
    wallet_id: str
    xp_balance: int
    reputation: float

    def to_profile(self) -> Dict[str, Any]:
        return {
            "user_identity": {
                "wallet_id": self.wallet_id,
                "xp_balance": self.xp_balance,
                "reputation_score": self.reputation,
            },
            "recent_events": [],
            "total_quests_completed": random.randint(0, 20),
            "average_completion_time": random.uniform(600, 7200),
        }


async def run_cycle(client: httpx.AsyncClient, user: User) -> None:
    quest_resp = await client.post("/quests/generate", json=user.to_profile())
    quest_resp.raise_for_status()
    economy_resp = await client.post(
        "/economy/simulate",
        json={
            "current_supply": random.randint(500_000, 2_000_000),
            "adoption_rate": random.uniform(1.0, 10.0),
            "days": 30,
            "iterations": 1000,
        },
    )
    economy_resp.raise_for_status()
    security_resp = await client.post(
        "/security/analyze",
        json={"user_id": user.wallet_id},
    )
    security_resp.raise_for_status()
    payload = {
        "quest": quest_resp.json(),
        "economy": economy_resp.json(),
        "security": security_resp.json(),
    }
    print(json.dumps(payload, indent=2)[:500])


async def main() -> None:
    users = [
        User(
            wallet_id=f"0xSIM{idx:04X}",
            xp_balance=random.randint(100, 5000),
            reputation=random.uniform(5, 95),
        )
        for idx in range(USERS)
    ]
    async with httpx.AsyncClient(base_url=API_BASE, timeout=60.0) as client:
        for cycle in range(CYCLES):
            print(f"Cycle {cycle + 1}/{CYCLES}")
            await asyncio.gather(*(run_cycle(client, user) for user in users))
            time.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
