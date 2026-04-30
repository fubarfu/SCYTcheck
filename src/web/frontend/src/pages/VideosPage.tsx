import { useEffect, useState } from "react";
import { deleteProject, getProjects } from "../services/api";
import type { ProjectListResponse, VideoProject } from "../types";

export function VideosPage() {
  const [projects, setProjects] = useState<VideoProject[]>([]);
  const [projectLocation, setProjectLocation] = useState("");
  const [locationStatus, setLocationStatus] = useState<ProjectListResponse["location_status"]>("unknown");
  const [loading, setLoading] = useState(true);
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);
  const [pendingDeleteProject, setPendingDeleteProject] = useState<VideoProject | null>(null);
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

  const handleDeleteProject = async (project: VideoProject) => {
    try {
      setDeletingProjectId(project.project_id);
      await deleteProject(project.project_id);
      await refresh();
    } catch (deleteError) {
      const message = deleteError instanceof Error ? deleteError.message : "Unable to delete project";
      setError(message);
    } finally {
      setDeletingProjectId(null);
      setPendingDeleteProject(null);
    }
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
              <strong>No videos analyzed yet.</strong>
              <p>Run an analysis to create your first project, or confirm the project location in Settings.</p>
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
                  <button
                    type="button"
                    className="ghost-action"
                    onClick={() => {
                      setPendingDeleteProject(project);
                    }}
                    disabled={deletingProjectId === project.project_id}
                  >
                    {deletingProjectId === project.project_id ? "Deleting..." : "Delete"}
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

      {pendingDeleteProject && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Delete project warning">
          <div className="modal-panel restore-confirmation-modal">
            <h3>Delete project</h3>
            <p>
              Delete project "{pendingDeleteProject.video_url}"?
              This will permanently remove all associated files from the project folder.
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="ghost-action"
                onClick={() => setPendingDeleteProject(null)}
                disabled={deletingProjectId === pendingDeleteProject.project_id}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-action"
                onClick={() => {
                  void handleDeleteProject(pendingDeleteProject);
                }}
                disabled={deletingProjectId === pendingDeleteProject.project_id}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
