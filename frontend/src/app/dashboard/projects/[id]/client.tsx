"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuthSafe } from "@/lib/auth";
import Link from "next/link";
import {
  getProject,
  submitPipeline,
  type Job,
  type ProjectDetail,
} from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function ProjectPage() {
  const params = useParams();
  const router = useRouter();
  const { getToken } = useAuthSafe();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadProject = useCallback(async () => {
    try {
      const token = await getToken();
      const data = await getProject(token, projectId);
      setProject(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [getToken, projectId]);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  useEffect(() => {
    if (!project) return;
    const hasActiveJobs = project.jobs.some(
      (j) => j.status === "queued" || j.status === "processing"
    );
    if (!hasActiveJobs) return;

    const interval = setInterval(loadProject, 5000);
    return () => clearInterval(interval);
  }, [project, loadProject]);

  async function handleUpload(file: File) {
    if (!file.name.match(/\.(mp4|mov)$/i)) {
      setError("Only MP4 and MOV files are supported.");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const token = await getToken();
      const job = await submitPipeline(token, projectId, file);
      router.push(`/dashboard/jobs/${job.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
  }

  if (loading) {
    return (
      <div className="text-on-surface-variant py-12 text-center font-display text-sm">
        Loading...
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-error py-12 text-center text-sm">
        {error || "Project not found"}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="text-sm text-on-surface-variant hover:text-primary transition-colors"
        >
          &larr; Back to projects
        </Link>
        <h1 className="font-display text-2xl font-bold tracking-tighter text-on-surface mt-2">
          {project.name}
        </h1>
        <p className="text-sm text-on-surface-variant mt-1 font-display">
          {project.source_language.toUpperCase()} →{" "}
          {project.target_languages.map((l) => l.toUpperCase()).join(", ")}
        </p>
      </div>

      {error && (
        <div className="bg-error/10 text-error ghost-border rounded-lg p-4 text-sm mb-6">
          {error}
        </div>
      )}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`mb-8 cursor-pointer rounded-lg border-2 border-dashed p-12 text-center transition-all duration-200 ${
          dragOver
            ? "border-primary bg-primary-container/10"
            : "border-outline-variant/30 hover:border-outline-variant/50 bg-surface-container"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp4,.mov"
          onChange={handleFileSelect}
          className="hidden"
        />
        {uploading ? (
          <p className="text-on-surface-variant text-sm">
            Uploading and starting pipeline...
          </p>
        ) : (
          <>
            <p className="text-on-surface font-display font-bold text-sm uppercase tracking-wider">
              Drop a video file here, or click to browse
            </p>
            <p className="text-sm text-outline mt-2">MP4 or MOV, up to 10GB</p>
          </>
        )}
      </div>

      {project.jobs.length > 0 && (
        <div>
          <h2 className="font-display text-lg font-bold tracking-tight text-on-surface mb-4">
            JOBS
          </h2>
          <div className="space-y-3">
            {project.jobs.map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function JobRow({ job }: { job: Job }) {
  return (
    <Link
      href={`/dashboard/jobs/${job.id}`}
      className="block bg-surface-container rounded-lg p-4 hover:bg-surface-container-high transition-all duration-200"
    >
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-display font-bold text-on-surface">
            {job.job_type === "full_pipeline" ? "Full Localization" : "Transcription"}
          </span>
          {job.duration_seconds && (
            <span className="text-sm text-on-surface-variant ml-3 font-display">
              {Math.round(job.duration_seconds / 60)} min
            </span>
          )}
          {job.cost_usd != null && (
            <span className="text-sm text-on-surface-variant ml-3 font-display">
              ${job.cost_usd.toFixed(4)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <Badge status={job.status} />
          <span className="text-xs text-outline font-display">
            {new Date(job.created_at).toLocaleString()}
          </span>
        </div>
      </div>
      {job.error_message && (
        <p className="text-sm text-error mt-2">{job.error_message}</p>
      )}
    </Link>
  );
}
