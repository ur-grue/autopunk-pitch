"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useAuthSafe } from "@/lib/auth";
import Link from "next/link";
import {
  getJob,
  getJobLanguages,
  getExportUrl,
  type Job,
  type LanguagesResponse,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export default function JobPage() {
  const params = useParams();
  const { getToken } = useAuthSafe();
  const jobId = params.id as string;

  const [job, setJob] = useState<Job | null>(null);
  const [languages, setLanguages] = useState<LanguagesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadJob = useCallback(async () => {
    try {
      const token = await getToken();
      const jobData = await getJob(token, jobId);
      setJob(jobData);

      if (jobData.status === "completed" && jobData.job_type === "full_pipeline") {
        const langData = await getJobLanguages(token, jobId);
        setLanguages(langData);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load job");
    } finally {
      setLoading(false);
    }
  }, [getToken, jobId]);

  useEffect(() => {
    loadJob();
  }, [loadJob]);

  useEffect(() => {
    if (!job) return;
    if (job.status !== "queued" && job.status !== "processing") return;

    const interval = setInterval(loadJob, 5000);
    return () => clearInterval(interval);
  }, [job, loadJob]);

  if (loading) {
    return (
      <div className="text-on-surface-variant py-12 text-center font-display text-sm">
        Loading...
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-error py-12 text-center text-sm">
        {error || "Job not found"}
      </div>
    );
  }

  const isActive = job.status === "queued" || job.status === "processing";

  return (
    <div className="max-w-3xl">
      <Link
        href={`/dashboard/projects/${job.project_id}`}
        className="text-sm text-on-surface-variant hover:text-primary transition-colors"
      >
        &larr; Back to project
      </Link>

      <div className="mt-4 mb-8">
        <h1 className="font-display text-2xl font-bold tracking-tighter text-on-surface">
          {job.job_type === "full_pipeline" ? "LOCALIZATION JOB" : "TRANSCRIPTION JOB"}
        </h1>
        <p className="text-xs text-outline mt-1 font-display tracking-wider">{job.id}</p>
      </div>

      {error && (
        <div className="bg-error/10 text-error ghost-border rounded-lg p-4 text-sm mb-6">
          {error}
        </div>
      )}

      <Card hover={false} className="mb-6">
        <div className="grid grid-cols-2 gap-6">
          <div>
            <span className="label-uppercase text-outline">Status</span>
            <p className="mt-2">
              <Badge status={job.status} />
            </p>
          </div>
          <div>
            <span className="label-uppercase text-outline">Type</span>
            <p className="mt-2 text-sm font-display text-on-surface">
              {job.job_type === "full_pipeline" ? "Full Localization" : "Transcription"}
            </p>
          </div>
          {job.duration_seconds && (
            <div>
              <span className="label-uppercase text-outline">Duration</span>
              <p className="mt-2 text-sm font-display text-on-surface">
                {formatDuration(job.duration_seconds)}
              </p>
            </div>
          )}
          {job.cost_usd != null && (
            <div>
              <span className="label-uppercase text-outline">Cost</span>
              <p className="mt-2 text-sm font-display text-tertiary">
                ${job.cost_usd.toFixed(4)}
              </p>
            </div>
          )}
          <div>
            <span className="label-uppercase text-outline">Created</span>
            <p className="mt-2 text-sm font-display text-on-surface-variant">
              {new Date(job.created_at).toLocaleString()}
            </p>
          </div>
          {job.completed_at && (
            <div>
              <span className="label-uppercase text-outline">Completed</span>
              <p className="mt-2 text-sm font-display text-on-surface-variant">
                {new Date(job.completed_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {job.error_message && (
          <div className="mt-4 bg-error/10 rounded-lg p-4 text-sm text-error">
            {job.error_message}
          </div>
        )}
      </Card>

      {isActive && (
        <div className="bg-tertiary-container/20 rounded-lg p-6 mb-6 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent mb-3" />
          <p className="text-sm text-tertiary font-display">
            {job.status === "queued"
              ? "Job is queued, waiting to start..."
              : "Processing your video. This may take a few minutes..."}
          </p>
        </div>
      )}

      {job.status === "completed" && languages && (
        <Card hover={false}>
          <h2 className="font-display text-lg font-bold tracking-tight text-on-surface mb-4">
            DOWNLOAD SUBTITLES
          </h2>
          <p className="label-uppercase text-outline mb-4">
            Source: {languages.source_language.toUpperCase()}
          </p>
          <div className="space-y-3">
            <DownloadRow
              language={languages.source_language}
              label="Source transcript"
              jobId={jobId}
            />
            {languages.target_languages.map((lang) => (
              <DownloadRow key={lang} language={lang} jobId={jobId} />
            ))}
          </div>
        </Card>
      )}

      {job.status === "completed" && !languages && job.job_type === "transcription" && (
        <Card hover={false}>
          <h2 className="font-display text-lg font-bold tracking-tight text-on-surface mb-4">
            DOWNLOAD TRANSCRIPT
          </h2>
          <DownloadRow language="source" label="Transcript" jobId={jobId} />
        </Card>
      )}
    </div>
  );
}

function DownloadRow({
  language,
  label,
  jobId,
}: {
  language: string;
  label?: string;
  jobId: string;
}) {
  return (
    <div className="flex items-center justify-between bg-surface-container-high rounded-lg p-3">
      <span className="text-sm font-display font-bold text-on-surface">
        {label || language.toUpperCase()}
      </span>
      <div className="flex gap-2">
        <Link
          href={`/dashboard/jobs/${jobId}/edit/${language}`}
          className="bg-primary-container/30 text-primary px-3 py-1 text-xs font-display font-bold uppercase tracking-wider rounded hover:bg-primary-container/50 transition-all"
        >
          Edit
        </Link>
        <a
          href={getExportUrl(jobId, language, "srt")}
          download
          className="ghost-border text-on-surface-variant px-3 py-1 text-xs font-display uppercase tracking-wider rounded hover:bg-surface-bright transition-all"
        >
          SRT
        </a>
        <a
          href={getExportUrl(jobId, language, "webvtt")}
          download
          className="ghost-border text-on-surface-variant px-3 py-1 text-xs font-display uppercase tracking-wider rounded hover:bg-surface-bright transition-all"
        >
          WebVTT
        </a>
      </div>
    </div>
  );
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}
