import type {
  AnalysisProgress,
  AppSettings,
  ProjectListResponse,
  ReviewContext,
} from "../types";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  const payload = (await response.json()) as T & { message?: string };
  if (!response.ok) {
    const message = (payload as { message?: string }).message ?? `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

export function startAnalysis(payload: Record<string, unknown>) {
  return requestJson<{ run_id: string; project_status?: string; message?: string }>(
    "/api/analysis/start",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export function getProgress(runId: string) {
  return requestJson<AnalysisProgress>(`/api/analysis/progress/${encodeURIComponent(runId)}`);
}

export function getProjects() {
  return requestJson<ProjectListResponse>("/api/projects");
}

export function deleteProject(projectId: string) {
  return requestJson<{ project_id: string; deleted: boolean }>(
    `/api/projects/${encodeURIComponent(projectId)}`,
    {
      method: "DELETE",
    },
  );
}

export function getSettings() {
  return requestJson<AppSettings>("/api/settings");
}

export function updateSettings(payload: Partial<AppSettings>) {
  return requestJson<AppSettings>("/api/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function validateSettings(payload: { project_location: string }) {
  return requestJson<{ project_location: string; location_status: AppSettings["location_status"]; message: string }>(
    "/api/settings/validate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
}

export function getReviewContext(videoId: string) {
  return requestJson<ReviewContext>(`/api/review/context?video_id=${encodeURIComponent(videoId)}`);
}
