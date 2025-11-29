type QuestCard = {
  quest_id?: string;
  wallet_id?: string;
  cohort?: string;
  difficulty_rating?: number;
};

interface Props {
  quests: QuestCard[];
}

const columns = [
  { key: "rookie", label: "Rookie" },
  { key: "core", label: "Core" },
  { key: "elite", label: "Elite" },
];

export function Kanban({ quests }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {columns.map((column) => (
        <div key={column.key} className="rounded-2xl border border-white/5 bg-white/5 p-4">
          <div className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
            {column.label}
          </div>
          <div className="space-y-3">
            {quests
              .filter((quest) => quest.cohort === column.key)
              .slice(0, 4)
              .map((quest) => (
                <div key={quest.quest_id} className="rounded-xl border border-white/10 bg-slate-900/40 p-3">
                  <div className="text-xs text-slate-400">{quest.wallet_id}</div>
                  <div className="text-lg font-semibold text-white">{quest.quest_id?.slice(0, 8)}...</div>
                  <div className="text-xs text-slate-500">Difficulty {quest.difficulty_rating}</div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
}
