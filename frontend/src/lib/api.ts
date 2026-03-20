// API Client for Autopunk Localize
// In demo mode (no NEXT_PUBLIC_API_URL), returns mock data for static preview

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";
const DEMO_MODE = !API_BASE;

// ── Types ──────────────────────────────────────────────

export type Project = {
  id: string;
  name: string;
  source_language: string;
  target_languages: string[];
  status: string;
  created_at: string;
  updated_at: string;
};

export type ProjectDetail = Project & {
  jobs: Job[];
};

export type Job = {
  id: string;
  project_id: string;
  job_type: "transcription" | "full_pipeline";
  status: "queued" | "processing" | "completed" | "failed";
  duration_seconds: number | null;
  cost_usd: number | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type SubtitleCue = {
  id: string;
  index: number;
  start_ms: number;
  end_ms: number;
  text: string;
  language: string;
  speaker: string | null;
  confidence: number | null;
  flags: string[] | null;
};

export type SubtitleListResponse = {
  job_id: string;
  language: string;
  total: number;
  subtitles: SubtitleCue[];
};

export type LanguagesResponse = {
  job_id: string;
  source_language: string;
  target_languages: string[];
};

// ── Mock Data ──────────────────────────────────────────

const MOCK_PROJECT: ProjectDetail = {
  id: "d1a2b3c4-5678-90ab-cdef-111111111111",
  name: "Lost in Translation — Season 1",
  source_language: "en",
  target_languages: ["fr", "es", "de"],
  status: "active",
  created_at: "2026-03-18T10:00:00Z",
  updated_at: "2026-03-18T10:00:00Z",
  jobs: [
    {
      id: "a1b2c3d4-5678-90ab-cdef-222222222222",
      project_id: "d1a2b3c4-5678-90ab-cdef-111111111111",
      job_type: "full_pipeline",
      status: "completed",
      duration_seconds: 3124,
      cost_usd: 1.76,
      error_message: null,
      started_at: "2026-03-18T10:01:00Z",
      completed_at: "2026-03-18T10:04:32Z",
      created_at: "2026-03-18T10:00:30Z",
      updated_at: "2026-03-18T10:04:32Z",
    },
    {
      id: "b2c3d4e5-5678-90ab-cdef-333333333333",
      project_id: "d1a2b3c4-5678-90ab-cdef-111111111111",
      job_type: "full_pipeline",
      status: "processing",
      duration_seconds: null,
      cost_usd: null,
      error_message: null,
      started_at: "2026-03-20T09:12:00Z",
      completed_at: null,
      created_at: "2026-03-20T09:11:45Z",
      updated_at: "2026-03-20T09:12:00Z",
    },
  ],
};

const MOCK_PROJECT_2: ProjectDetail = {
  id: "e5f6a7b8-5678-90ab-cdef-444444444444",
  name: "Neon District — EP03",
  source_language: "en",
  target_languages: ["ja", "ko"],
  status: "draft",
  created_at: "2026-03-15T14:30:00Z",
  updated_at: "2026-03-15T14:30:00Z",
  jobs: [],
};

const MOCK_SUBTITLES: SubtitleCue[] = [
  {
    id: "sub-001",
    index: 1,
    start_ms: 1200,
    end_ms: 4800,
    text: "Dans les rues sombres de la ville,",
    language: "fr",
    speaker: "NARRATOR",
    confidence: -0.3,
    flags: [],
  },
  {
    id: "sub-002",
    index: 2,
    start_ms: 5000,
    end_ms: 8200,
    text: "un signal lumineux traversa le ciel nocturne.",
    language: "fr",
    speaker: "NARRATOR",
    confidence: -0.5,
    flags: [],
  },
  {
    id: "sub-003",
    index: 3,
    start_ms: 9500,
    end_ms: 12800,
    text: "\"Est-ce que tu l'as vu ?\" murmura-t-elle.",
    language: "fr",
    speaker: "ELENA",
    confidence: -0.4,
    flags: [],
  },
  {
    id: "sub-004",
    index: 4,
    start_ms: 13200,
    end_ms: 16500,
    text: "Le protocole NEXUS était activé.",
    language: "fr",
    speaker: null,
    confidence: -1.5,
    flags: ["cultural_ref"],
  },
  {
    id: "sub-005",
    index: 5,
    start_ms: 17000,
    end_ms: 21400,
    text: "Il n'y avait plus de retour en arrière possible.",
    language: "fr",
    speaker: "NARRATOR",
    confidence: -0.2,
    flags: [],
  },
  {
    id: "sub-006",
    index: 6,
    start_ms: 22000,
    end_ms: 26800,
    text: "Les capteurs indiquaient une température\nde moins quarante degrés Fahrenheit.",
    language: "fr",
    speaker: "TECH",
    confidence: -0.8,
    flags: ["unit_conversion"],
  },
  {
    id: "sub-007",
    index: 7,
    start_ms: 27500,
    end_ms: 31200,
    text: "\"Nous devons agir maintenant,\" dit le commandant.",
    language: "fr",
    speaker: "COMMANDER",
    confidence: -0.3,
    flags: [],
  },
  {
    id: "sub-008",
    index: 8,
    start_ms: 32000,
    end_ms: 36400,
    text: "L'opération Night Owl était la dernière chance\nde sauver la station.",
    language: "fr",
    speaker: "NARRATOR",
    confidence: -1.2,
    flags: ["low_confidence", "cultural_ref"],
  },
];

// ── Fetch Helper ───────────────────────────────────────

async function apiFetch<T>(
  path: string,
  token: string | null,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }

  return res.json();
}

// ── API Functions ──────────────────────────────────────

export async function listProjects(
  token: string | null
): Promise<Project[]> {
  if (DEMO_MODE) {
    return [MOCK_PROJECT, MOCK_PROJECT_2];
  }
  return apiFetch<Project[]>("/api/v1/projects", token);
}

export async function createProject(
  token: string | null,
  data: { name: string; source_language: string; target_languages: string[] }
): Promise<Project> {
  if (DEMO_MODE) {
    return {
      id: crypto.randomUUID(),
      ...data,
      status: "draft",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  return apiFetch<Project>("/api/v1/projects", token, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getProject(
  token: string | null,
  id: string
): Promise<ProjectDetail> {
  if (DEMO_MODE) {
    const p = [MOCK_PROJECT, MOCK_PROJECT_2].find((p) => p.id === id);
    return p || MOCK_PROJECT;
  }
  return apiFetch<ProjectDetail>(`/api/v1/projects/${id}`, token);
}

export async function getJob(
  token: string | null,
  id: string
): Promise<Job> {
  if (DEMO_MODE) {
    const job = MOCK_PROJECT.jobs.find((j) => j.id === id);
    return job || MOCK_PROJECT.jobs[0];
  }
  return apiFetch<Job>(`/api/v1/jobs/${id}`, token);
}

export async function getJobLanguages(
  token: string | null,
  jobId: string
): Promise<LanguagesResponse> {
  if (DEMO_MODE) {
    return {
      job_id: jobId,
      source_language: "en",
      target_languages: ["fr", "es", "de"],
    };
  }
  return apiFetch<LanguagesResponse>(`/api/v1/jobs/${jobId}/languages`, token);
}

export async function submitPipeline(
  token: string | null,
  projectId: string,
  file: File
): Promise<Job> {
  if (DEMO_MODE) {
    return MOCK_PROJECT.jobs[1];
  }

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/jobs/localize`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

export async function listSubtitles(
  token: string | null,
  jobId: string,
  language: string
): Promise<SubtitleListResponse> {
  if (DEMO_MODE) {
    return {
      job_id: jobId,
      language,
      total: MOCK_SUBTITLES.length,
      subtitles: MOCK_SUBTITLES,
    };
  }
  return apiFetch<SubtitleListResponse>(
    `/api/v1/jobs/${jobId}/subtitles/${language}`,
    token
  );
}

export async function updateSubtitle(
  token: string | null,
  id: string,
  data: { text?: string; start_ms?: number; end_ms?: number }
): Promise<SubtitleCue> {
  if (DEMO_MODE) {
    const cue = MOCK_SUBTITLES.find((s) => s.id === id)!;
    return { ...cue, ...data };
  }
  return apiFetch<SubtitleCue>(`/api/v1/subtitles/${id}`, token, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function splitSubtitle(
  token: string | null,
  id: string,
  data: { split_at_ms: number; first_text: string; second_text: string }
): Promise<SubtitleCue[]> {
  if (DEMO_MODE) {
    const cue = MOCK_SUBTITLES.find((s) => s.id === id)!;
    return [
      { ...cue, end_ms: data.split_at_ms, text: data.first_text },
      {
        ...cue,
        id: cue.id + "-b",
        index: cue.index + 1,
        start_ms: data.split_at_ms,
        text: data.second_text,
      },
    ];
  }
  return apiFetch<SubtitleCue[]>(`/api/v1/subtitles/${id}/split`, token, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function mergeSubtitle(
  token: string | null,
  id: string
): Promise<SubtitleCue> {
  if (DEMO_MODE) {
    const cue = MOCK_SUBTITLES.find((s) => s.id === id)!;
    return cue;
  }
  return apiFetch<SubtitleCue>(`/api/v1/subtitles/${id}/merge`, token, {
    method: "POST",
  });
}

export function getExportUrl(
  jobId: string,
  language: string,
  format: "srt" | "webvtt"
): string {
  if (DEMO_MODE) return "#";
  return `${API_BASE}/api/v1/jobs/${jobId}/export/${language}?format=${format}`;
}
