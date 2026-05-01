import { useEffect, useMemo, useState } from "react";
import { getSettings, updateSettings, validateSettings } from "../services/api";
import type { AppSettings } from "../types";

export function SettingsPage() {
  const [projectLocation, setProjectLocation] = useState("");
  const [savedLocation, setSavedLocation] = useState("");
  const [defaultLocation, setDefaultLocation] = useState("");
  const [locationStatus, setLocationStatus] = useState<AppSettings["location_status"]>("unknown");
  const [validationMessage, setValidationMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = useMemo(() => {
    return !saving && projectLocation.trim().length > 0 && projectLocation.trim() !== savedLocation;
  }, [projectLocation, savedLocation, saving]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const settings = await getSettings();
        const currentLocation = String(settings.project_location || "");
        setProjectLocation(currentLocation);
        setSavedLocation(currentLocation);
        setDefaultLocation(String(settings.default_project_location || currentLocation));
        setLocationStatus(settings.location_status);
        setValidationMessage(`Current location is ${settings.location_status}.`);
        setError(null);
      } catch (loadError) {
        const message = loadError instanceof Error ? loadError.message : "Unable to load settings";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const runValidation = async (candidate: string) => {
    try {
      const result = await validateSettings({ project_location: candidate.trim() });
      setLocationStatus(result.location_status);
      setValidationMessage(result.message);
      setError(null);
    } catch (validationError) {
      const message = validationError instanceof Error ? validationError.message : "Validation failed";
      setError(message);
    }
  };

  const handleBrowse = async () => {
    const params = projectLocation.trim()
      ? `?initial_dir=${encodeURIComponent(projectLocation.trim())}`
      : "";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 180_000);

    try {
      const response = await fetch(`/api/fs/pick-folder${params}`, { signal: controller.signal });
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as { path?: string };
      if (payload.path) {
        setProjectLocation(payload.path);
        await runValidation(payload.path);
      }
    } finally {
      clearTimeout(timeout);
    }
  };

  const handleResetDefault = async () => {
    const next = defaultLocation || savedLocation;
    setProjectLocation(next);
    await runValidation(next);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const updated = await updateSettings({ project_location: projectLocation.trim() });
      setSavedLocation(String(updated.project_location || ""));
      setProjectLocation(String(updated.project_location || ""));
      setDefaultLocation(String(updated.default_project_location || defaultLocation));
      setLocationStatus(updated.location_status);
      setValidationMessage("Project location saved.");
      setError(null);
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "Failed to save settings";
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="page-panel">
      <div className="page-heading-row">
        <h2>Settings</h2>
        <p className="page-subtitle">
          Configure where video projects are stored and validated for discovery.
        </p>
      </div>

      {error && <div className="session-load-error">{error}</div>}

      <div className="panel-card">
        <div className="panel-card-body form-stack">
          {loading ? (
            <p>Loading settings…</p>
          ) : (
            <>
              <label>
                Project location
                <div className="output-folder-row">
                  <input
                    className="output-folder-input"
                    type="text"
                    value={projectLocation}
                    onChange={(event) => setProjectLocation(event.target.value)}
                    onBlur={() => { void runValidation(projectLocation); }}
                    placeholder="C:/Users/<you>/AppData/Roaming/SCYTcheck/projects"
                  />
                  <button type="button" className="btn-secondary output-folder-button" onClick={() => { void handleBrowse(); }}>
                    Browse…
                  </button>
                </div>
              </label>

              <div className="review-progress-meta">
                <span className={`status-chip status-${locationStatus}`}>Status: {locationStatus}</span>
                <span>{validationMessage}</span>
              </div>

              <div className="candidate-list-actions">
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => { void runValidation(projectLocation); }}
                >
                  Validate
                </button>
                <button type="button" className="ghost-action" onClick={() => { void handleResetDefault(); }}>
                  Reset to Default
                </button>
                <button type="button" className="primary-action" disabled={!canSave} onClick={() => { void handleSave(); }}>
                  {saving ? "Saving…" : "Save Settings"}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
