import { ReactNode } from "react";

interface CardProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}

export function Card({ title, subtitle, children }: CardProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/5 p-6 shadow-xl shadow-slate-950/60">
      <div className="mb-2 text-sm uppercase tracking-wide text-slate-400">{title}</div>
      {subtitle && <div className="text-3xl font-semibold text-white">{subtitle}</div>}
      {children}
    </div>
  );
}
