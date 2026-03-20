"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { listProjects, type Project } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const { getToken } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken();
        const data = await listProjects(token);
        setProjects(data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load projects");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [getToken]);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="text-on-surface-variant font-display text-sm">Loading projects...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-error/10 text-error ghost-border rounded-lg p-4 text-sm">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display text-2xl font-bold tracking-tighter text-on-surface">
          PROJECTS
        </h1>
        <Link
          href="/dashboard/new"
          className="btn-gradient font-display px-4 py-2 text-xs font-bold uppercase tracking-[0.15em] rounded hover:shadow-glow active:scale-[0.98] transition-all duration-200"
        >
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-on-surface-variant mb-4 text-sm">No projects yet.</p>
          <Link
            href="/dashboard/new"
            className="text-tertiary font-bold hover:underline underline-offset-4 text-sm"
          >
            Create your first project
          </Link>
        </div>
      ) : (
        <div className="grid gap-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/dashboard/projects/${project.id}`}
              className="block bg-surface-container rounded-lg p-6 hover:bg-surface-container-high transition-all duration-200"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-display font-bold tracking-tight text-on-surface">
                    {project.name}
                  </h2>
                  <p className="text-sm text-on-surface-variant mt-1 font-display">
                    {project.source_language.toUpperCase()} →{" "}
                    {project.target_languages.map((l) => l.toUpperCase()).join(", ")}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Badge status={project.status} />
                  <span className="text-xs text-outline font-display">
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
