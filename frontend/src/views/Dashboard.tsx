import { useMemo } from "react";
import { Card } from "../components/Card";
import { Kanban } from "../components/Kanban";
import { ComplexTable } from "../components/ComplexTable";
import { useAgentStream } from "../hooks/useAgentStream";

export function Dashboard() {
  const events = useAgentStream({});

  const quests = useMemo(
    () => events.filter((event) => event.event === "quest.generated").map((event) => event.payload),
    [events]
  );

  const security = useMemo(
    () => events.filter((event) => event.event === "security.alert").map((event) => event.payload),
    [events]
  );

  const economy = events.find((event) => event.event === "economy.simulation")?.payload;

  return (
    <div className="space-y-8">
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Predicted Inflation" subtitle={`${economy?.predicted_inflation ?? '--'} %`} />
        <Card title="Active Quests" subtitle={`${quests.length}`} />
        <Card title="Security Alerts" subtitle={`${security.length}`} />
      </div>

      <Kanban quests={quests as any} />

      <div className="rounded-2xl border border-white/5 bg-white/5 p-6">
        <div className="mb-4 text-sm uppercase tracking-wide text-slate-400">Security Activity</div>
        <ComplexTable rows={security as any} />
      </div>
    </div>
  );
}
