"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { createProject } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input, Select, Label } from "@/components/ui/input";

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "fr", name: "French" },
  { code: "es", name: "Spanish" },
  { code: "de", name: "German" },
  { code: "it", name: "Italian" },
  { code: "pt", name: "Portuguese" },
  { code: "ja", name: "Japanese" },
  { code: "ko", name: "Korean" },
  { code: "zh", name: "Chinese" },
  { code: "hi", name: "Hindi" },
  { code: "ar", name: "Arabic" },
  { code: "ru", name: "Russian" },
  { code: "nl", name: "Dutch" },
  { code: "pl", name: "Polish" },
  { code: "th", name: "Thai" },
];

export default function NewProjectPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const [name, setName] = useState("");
  const [sourceLanguage, setSourceLanguage] = useState("en");
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function toggleLanguage(code: string) {
    setTargetLanguages((prev) =>
      prev.includes(code)
        ? prev.filter((l) => l !== code)
        : prev.length < 10
        ? [...prev, code]
        : prev
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || targetLanguages.length === 0) return;

    setSubmitting(true);
    setError(null);

    try {
      const token = await getToken();
      const project = await createProject(token, {
        name: name.trim(),
        source_language: sourceLanguage,
        target_languages: targetLanguages,
      });
      router.push(`/dashboard/projects/${project.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create project");
      setSubmitting(false);
    }
  }

  const availableTargets = LANGUAGES.filter((l) => l.code !== sourceLanguage);

  return (
    <div className="max-w-2xl">
      <h1 className="font-display text-2xl font-bold tracking-tighter text-on-surface mb-8">
        NEW PROJECT
      </h1>

      <form onSubmit={handleSubmit} className="space-y-8">
        {error && (
          <div className="bg-error/10 text-error ghost-border rounded-lg p-4 text-sm">
            {error}
          </div>
        )}

        <div>
          <Label htmlFor="name">Project Name</Label>
          <Input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My Documentary"
            required
          />
        </div>

        <div>
          <Label htmlFor="source">Source Language</Label>
          <Select
            id="source"
            value={sourceLanguage}
            onChange={(e) => {
              setSourceLanguage(e.target.value);
              setTargetLanguages((prev) =>
                prev.filter((l) => l !== e.target.value)
              );
            }}
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.name}
              </option>
            ))}
          </Select>
        </div>

        <div>
          <Label>
            Target Languages ({targetLanguages.length}/10)
          </Label>
          <div className="flex flex-wrap gap-2 mt-1">
            {availableTargets.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => toggleLanguage(lang.code)}
                className={`px-3 py-1.5 text-xs font-display uppercase tracking-wider rounded transition-all duration-200 ${
                  targetLanguages.includes(lang.code)
                    ? "bg-primary-container text-primary shadow-glow-sm"
                    : "ghost-border text-on-surface-variant hover:bg-surface-container-high"
                }`}
              >
                {lang.name}
              </button>
            ))}
          </div>
        </div>

        <Button
          type="submit"
          disabled={submitting || !name.trim() || targetLanguages.length === 0}
          className="w-full"
        >
          {submitting ? "Creating..." : "Create Project"}
        </Button>
      </form>
    </div>
  );
}
