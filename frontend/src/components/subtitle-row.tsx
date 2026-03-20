"use client";

import { useRef, useState } from "react";
import type { SubtitleCue } from "@/lib/api";

function formatTimecode(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const msRem = ms % 1000;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(msRem).padStart(3, "0")}`;
}

export function SubtitleRow({
  cue,
  isActive,
  onUpdate,
  onSplit,
  onMerge,
  onClick,
}: {
  cue: SubtitleCue;
  isActive: boolean;
  onUpdate: (id: string, data: { text?: string; start_ms?: number; end_ms?: number }) => Promise<void>;
  onSplit: (id: string) => Promise<void>;
  onMerge: (id: string) => Promise<void>;
  onClick: (cue: SubtitleCue) => void;
}) {
  const [text, setText] = useState(cue.text);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const hasFlagsBadge =
    (cue.flags && cue.flags.length > 0) ||
    (cue.confidence !== null && cue.confidence < -1.0);

  async function handleBlur() {
    if (text !== cue.text) {
      await onUpdate(cue.id, { text });
    }
  }

  return (
    <div
      onClick={() => onClick(cue)}
      className={`group rounded-lg p-3 transition-all duration-150 cursor-pointer ${
        isActive
          ? "bg-primary/5 border border-primary/30"
          : "bg-surface-container ghost-border hover:bg-surface-container-high"
      }`}
    >
      <div className="flex items-start gap-3">
        {/* Index */}
        <span className="shrink-0 w-8 h-8 rounded bg-surface-container-high flex items-center justify-center text-[11px] font-display font-bold text-outline">
          {cue.index}
        </span>

        {/* Timecodes */}
        <div className="shrink-0 flex flex-col gap-0.5">
          <span className="text-[10px] font-display text-on-surface-variant tracking-wider">
            {formatTimecode(cue.start_ms)}
          </span>
          <span className="text-[10px] font-display text-outline tracking-wider">
            {formatTimecode(cue.end_ms)}
          </span>
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <textarea
            ref={textRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onBlur={handleBlur}
            rows={Math.min(text.split("\n").length + 1, 4)}
            className="w-full bg-transparent text-sm text-on-surface font-body resize-none focus:outline-none focus:ring-1 focus:ring-primary/20 rounded px-2 py-1 -mx-2 -my-1"
          />

          {/* Flags */}
          {hasFlagsBadge && (
            <div className="flex gap-1.5 mt-1.5">
              {cue.flags?.map((flag) => (
                <span
                  key={flag}
                  className="text-[9px] font-display uppercase tracking-wider px-1.5 py-0.5 rounded bg-tertiary/15 text-tertiary border border-tertiary/20"
                >
                  {flag.replace(/_/g, " ")}
                </span>
              ))}
              {cue.confidence !== null && cue.confidence < -1.0 && (
                <span className="text-[9px] font-display uppercase tracking-wider px-1.5 py-0.5 rounded bg-error/15 text-error border border-error/20">
                  low confidence
                </span>
              )}
            </div>
          )}
        </div>

        {/* Speaker */}
        {cue.speaker && (
          <span className="shrink-0 text-[9px] font-display uppercase tracking-wider text-outline bg-surface-container-high px-2 py-0.5 rounded">
            {cue.speaker}
          </span>
        )}

        {/* Actions */}
        <div className="shrink-0 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSplit(cue.id);
            }}
            title="Split"
            className="ghost-border text-on-surface-variant px-2 py-1 text-[10px] font-display uppercase tracking-wider rounded hover:bg-surface-bright transition-all"
          >
            Split
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onMerge(cue.id);
            }}
            title="Merge with next"
            className="ghost-border text-on-surface-variant px-2 py-1 text-[10px] font-display uppercase tracking-wider rounded hover:bg-surface-bright transition-all"
          >
            Merge
          </button>
        </div>
      </div>
    </div>
  );
}
