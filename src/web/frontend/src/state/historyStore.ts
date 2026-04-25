export interface HistoryEntry {
  history_id: string;
  display_name: string;
  canonical_source: string;
  duration_seconds: number | null;
  potential_duplicate: boolean;
  run_count: number;
  output_folder: string;
  updated_at: string;
}

export interface HistoryListResponse {
  items: HistoryEntry[];
  total: number;
}

export interface ReopenResponse {
  history_id: string;
  analysis_context: {
    source_type: "youtube_url" | "local_file";
    source_value: string;
    scan_region: { x: number; y: number; width: number; height: number };
    output_folder: string;
    context_patterns: Array<Record<string, unknown>>;
    analysis_settings: Record<string, unknown>;
  };
  derived_results: {
    resolution_status: "ready" | "partial" | "missing_results" | "missing_folder";
    resolved_csv_paths: string[];
    resolved_sidecar_paths?: string[];
    primary_csv_path?: string | null;
    resolution_messages: string[];
  };
  review_route: string;
}

export interface HistoryStoreState {
  items: HistoryEntry[];
  total: number;
  loading: boolean;
  error: string | null;
}

export const initialHistoryStoreState: HistoryStoreState = {
  items: [],
  total: 0,
  loading: false,
  error: null,
};

export async function listHistory(limit = 200): Promise<HistoryListResponse> {
  const response = await fetch(`/api/history/videos?limit=${encodeURIComponent(String(limit))}`);
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(body.message ?? "Unable to load history");
  }
  return (await response.json()) as HistoryListResponse;
}

export async function reopenHistory(historyId: string): Promise<ReopenResponse> {
  const response = await fetch("/api/history/reopen", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ history_id: historyId }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(body.message ?? "Unable to open history entry");
  }
  return (await response.json()) as ReopenResponse;
}

export async function deleteHistory(historyId: string): Promise<void> {
  const response = await fetch(`/api/history/videos/${encodeURIComponent(historyId)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(body.message ?? "Unable to delete history entry");
  }
}
