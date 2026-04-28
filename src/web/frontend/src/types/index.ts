export interface AnalysisProgress {
  status: "in_progress" | "completed" | "failed";
  progress_percent: number;
  project_status: "creating" | "merging";
  message: string;
  frame_count?: number;
  frames_processed?: number;
  candidates_found?: number;
  elapsed_ms?: number;
  estimated_remaining_ms?: number;
  review_ready?: boolean;
  video_id?: string;
}

export interface Candidate {
  candidate_id: string;
  spelling: string;
  discovered_in_run: string;
  marked_new: boolean;
  decision: "unreviewed" | "reviewed" | "confirmed" | "rejected" | "edited";
}

export interface CandidateGroup {
  group_id: string;
  candidate_ids: string[];
  decision: "unreviewed" | "reviewed" | "confirmed" | "rejected";
}

export interface ReviewContext {
  video_id: string;
  video_url: string;
  merged_timestamp: string;
  candidates: Candidate[];
  groups: CandidateGroup[];
}

export interface VideoProject {
  project_id: string;
  video_url: string;
  project_location: string;
  created_date: string;
  run_count: number;
  last_analyzed_at?: string;
}

export interface ProjectListResponse {
  projects: VideoProject[];
  location_status: "valid" | "missing" | "unwritable" | "unknown";
}

export interface AppSettings {
  project_location: string;
  is_default: boolean;
  validation_status: "valid" | "missing" | "unwritable" | "unknown";
}
