"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuthSafe } from "@/lib/auth";
import Link from "next/link";
import {
  getExportUrl,
  listSubtitles,
  mergeSubtitle,
  splitSubtitle,
  updateSubtitle,
  type SubtitleCue,
} from "@/lib/api";
import { SubtitleRow } from "@/components/subtitle-row";

export default function SubtitleEditorPage() {
  const params = useParams();
  const { getToken } = useAuthSafe();
  const jobId = params.id as string;
  const language = params.language as string;

  const [subtitles, setSubtitles] = useState<SubtitleCue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeCueId, setActiveCueId] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "flagged">("all");

  const loadSubtitles = useCallback(async () => {
    try {
      const token = await getToken();
      const data = await listSubtitles(token, jobId, language);
      setSubtitles(data.subtitles);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load subtitles");
    } finally {
      setLoading(false);
    }
  }, [getToken, jobId, language]);

  useEffect(() => {
    loadSubtitles();
  }, [loadSubtitles]);

  const handleUpdate = useCallback(
    async (
      id: string,
      data: { text?: string; start_ms?: number; end_ms?: number }
    ) => {
      setSaving(true);
      try {
        const token = await getToken();
        const updated = await updateSubtitle(token, id, data);
        setSubtitles((prev) =>
          prev.map((s) => (s.id === id ? updated : s))
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Save failed");
      } finally {
        setSaving(false);
      }
    },
    [getToken]
  );

  const handleSplit = useCallback(
    async (id: string) => {
      const cue = subtitles.find((s) => s.id === id);
      if (!cue) return;

      const midMs = Math.round((cue.start_ms + cue.end_ms) / 2);
      const words = cue.text.split(" ");
      const mid = Math.ceil(words.length / 2);
      const firstText = words.slice(0, mid).join(" ");
      const secondText = words.slice(mid).join(" ");

      setSaving(true);
      try {
        const token = await getToken();
        await splitSubtitle(token, id, {
          split_at_ms: midMs,
          first_text: firstText,
          second_text: secondText,
        });
        await loadSubtitles();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Split failed");
      } finally {
        setSaving(false);
      }
    },
    [getToken, subtitles, loadSubtitles]
  );

  const handleMerge = useCallback(
    async (id: string) => {
      setSaving(true);
      try {
        const token = await getToken();
        await mergeSubtitle(token, id);
        await loadSubtitles();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Merge failed");
      } finally {
        setSaving(false);
      }
    },
    [getToken, loadSubtitles]
  );

  const handleCueClick = useCallback((cue: SubtitleCue) => {
    setActiveCueId(cue.id);
  }, []);

  const filteredSubtitles =
    filter === "flagged"
      ? subtitles.filter(
          (s) =>
            (s.flags && s.flags.length > 0) ||
            (s.confidence !== null && s.confidence < -1.0)
        )
      : subtitles;

  const flaggedCount = subtitles.filter(
    (s) =>
      (s.flags && s.flags.length > 0) ||
      (s.confidence !== null && s.confidence < -1.0)
  ).length;

  if (loading) {
    return (
      <div className="text-on-surface-variant py-12 text-center font-display text-sm">
        Loading editor...
      </div>
    );
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <Link
          href={`/dashboard/jobs/${jobId}`}
          className="text-sm text-on-surface-variant hover:text-primary transition-colors"
        >
          &larr; Back to job
        </Link>
        <div className="flex items-center justify-between mt-2">
          <h1 className="font-display text-2xl font-bold tracking-tighter text-on-surface">
            SUBTITLE EDITOR — {language.toUpperCase()}
          </h1>
          <div className="flex items-center gap-3">
            {saving && (
              <span className="text-xs text-outline font-display animate-pulse">
                Saving...
              </span>
            )}
            <a
              href={getExportUrl(jobId, language, "srt")}
              download
              className="ghost-border text-on-surface-variant px-3 py-1.5 text-xs font-display uppercase tracking-wider rounded hover:bg-surface-container-high transition-all"
            >
              Export SRT
            </a>
            <a
              href={getExportUrl(jobId, language, "webvtt")}
              download
              className="ghost-border text-on-surface-variant px-3 py-1.5 text-xs font-display uppercase tracking-wider rounded hover:bg-surface-container-high transition-all"
            >
              Export WebVTT
            </a>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-error/10 text-error ghost-border rounded-lg p-3 text-sm mb-4">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 underline text-error/80 hover:text-error"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="flex items-center gap-4 mb-4 bg-surface-container-low rounded-lg p-3 ghost-border">
        <span className="text-sm text-on-surface-variant font-display">
          {subtitles.length} cues
        </span>
        <span className="text-sm text-outline-variant">|</span>
        <button
          onClick={() => setFilter("all")}
          className={`text-xs font-display uppercase tracking-wider px-3 py-1 rounded transition-all ${
            filter === "all"
              ? "bg-primary-container text-primary"
              : "text-on-surface-variant hover:bg-surface-container-high"
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter("flagged")}
          className={`text-xs font-display uppercase tracking-wider px-3 py-1 rounded transition-all ${
            filter === "flagged"
              ? "bg-tertiary-container text-tertiary"
              : "text-on-surface-variant hover:bg-surface-container-high"
          }`}
        >
          Flagged ({flaggedCount})
        </button>
        <div className="flex-1" />
        <span className="text-[10px] text-outline font-display tracking-wider uppercase">
          Changes auto-save
        </span>
      </div>

      <div className="space-y-2">
        {filteredSubtitles.map((cue) => (
          <SubtitleRow
            key={cue.id}
            cue={cue}
            isActive={cue.id === activeCueId}
            onUpdate={handleUpdate}
            onSplit={handleSplit}
            onMerge={handleMerge}
            onClick={handleCueClick}
          />
        ))}
      </div>

      {filteredSubtitles.length === 0 && (
        <div className="text-center py-12 text-on-surface-variant font-display text-sm">
          {filter === "flagged"
            ? "No flagged subtitles."
            : "No subtitles found."}
        </div>
      )}
    </div>
  );
}
