import { useEffect, useState } from "react";
import { getProjects } from "../services/api";
import type { ProjectListResponse, VideoProject } from "../types";

export function VideosPage() {
  const [projects, setProjects] = useState<VideoProject[]>([]);
  const [projectLocation, setProjectLocation] = useState("");
  const [locationStatus, setLocationStatus] = useState<ProjectListResponse["location_status"]>("unknown");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setLoading(true);
      const response = await getProjects();
      setProjects(response.projects || []);
      setProjectLocation(response.project_location || "");
      setLocationStatus(response.location_status || "unknown");
      setError(null);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "Unable to load projects";
      setError(message);
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const openProject = (projectId: string) => {
    window.location.hash = `#/review?video_id=${encodeURIComponent(projectId)}`;
  };

  return (
    <section className="page-panel">
      <div className="page-heading-row">
        <h2>Videos</h2>
        <p className="page-subtitle">
          Discover analyzed video projects from the configured location and open them directly in review.
        </p>
      </div>

      {error && <div className="session-load-error">{error}</div>}

      <div className="panel-card">
        <div className="panel-card-body review-topbar">
          <div className="review-summary-block">
            <div className="review-progress-meta">
              <span>Project location: {projectLocation || "(not configured)"}</span>
              <span>Status: {locationStatus}</span>
              <span>{projects.length} project(s)</span>
            </div>
          </div>
          <div className="candidate-list-actions">
            <button type="button" className="ghost-action" onClick={() => { void refresh(); }}>
              Refresh
            </button>
            {(locationStatus === "missing" || locationStatus === "unwritable") && (
              <button
                type="button"
                className="primary-action"
                onClick={() => {
                  window.location.hash = "#/settings";
                }}
              >
                Fix in Settings
              </button>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <div className="panel-card">
          <div className="panel-card-body">Loading projects…</div>
        </div>
      )}

      {!loading && projects.length === 0 && (
        <div className="panel-card">
          <div className="panel-card-body empty-region-state">
            <div>
              <strong>No projects found.</strong>
              <p>Run an analysis first, or update your project location in Settings.</p>
            </div>
          </div>
        </div>
      )}

      {!loading && projects.length > 0 && (
        <div className="history-list">
          {projects.map((project) => (
            <article key={project.project_id} className="history-entry" data-testid={`video-project-${project.project_id}`}>
              <header className="history-entry-header">
                <div>
                  <h3>{project.video_url}</h3>
                  <p className="history-entry-subtitle">Project ID: {project.project_id}</p>
                </div>
                <div className="history-entry-actions">
                  <button type="button" className="primary-action" onClick={() => openProject(project.project_id)}>
                    Open Project
                  </button>
                </div>
              </header>
              <div className="history-entry-grid">
                <div>
                  <span className="history-label">Runs</span>
                  <span>{project.run_count}</span>
                </div>
                <div>
                  <span className="history-label">Last analyzed</span>
                  <span>{(project as VideoProject & { last_analyzed?: string }).last_analyzed || "-"}</span>
                </div>
                <div>
                  <span className="history-label">Candidates reviewed</span>
                  <span>{(project as VideoProject & { candidate_count_reviewed?: number }).candidate_count_reviewed ?? 0}</span>
                </div>
                <div>
                  <span className="history-label">Candidates total</span>
                  <span>{(project as VideoProject & { candidate_count_total?: number }).candidate_count_total ?? 0}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
