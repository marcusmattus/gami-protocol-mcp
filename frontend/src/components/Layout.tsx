import { ReactNode } from "react";

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50">
      <aside className="fixed left-0 top-0 h-full w-64 border-r border-white/5 bg-slate-900/60 backdrop-blur">
        <div className="p-6 text-xl font-semibold tracking-tight">Gami Protocol</div>
        <nav className="px-6 space-y-2 text-sm text-slate-400">
          <div>Dashboard</div>
          <div>Quests</div>
          <div>Economy</div>
          <div>Security</div>
        </nav>
      </aside>
      <main className="pl-64">
        <header className="border-b border-white/5 bg-slate-900/50 px-8 py-4 backdrop-blur">
          <h1 className="text-2xl font-semibold">Supervisor Console</h1>
          <p className="text-sm text-slate-400">Streaming live from MCP + Google Cloud</p>
        </header>
        <section className="p-8">{children}</section>
      </main>
    </div>
  );
}
