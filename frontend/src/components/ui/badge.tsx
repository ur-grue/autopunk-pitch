const statusStyles: Record<string, string> = {
  completed:
    "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
  processing:
    "bg-primary/15 text-primary border-primary/20 animate-pulse",
  queued:
    "bg-outline/15 text-on-surface-variant border-outline/20",
  failed:
    "bg-error/15 text-error border-error/20",
  active:
    "bg-primary/15 text-primary border-primary/20",
  draft:
    "bg-outline/10 text-outline border-outline/15",
};

const fallback = "bg-outline/10 text-on-surface-variant border-outline/15";

export function Badge({ status }: { status: string }) {
  const style = statusStyles[status] || fallback;

  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-[10px] font-display font-bold uppercase tracking-widest border ${style}`}
    >
      {status}
    </span>
  );
}
