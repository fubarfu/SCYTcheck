from __future__ import annotations

from src.services.project_service import ProjectService
from src.web.api.routes.settings import SettingsHandler


class ProjectsHandler:
    def __init__(
        self,
        project_service: ProjectService | None = None,
        settings_handler: SettingsHandler | None = None,
    ) -> None:
        self.project_service = project_service or ProjectService()
        self.settings_handler = settings_handler or SettingsHandler()

    def get_projects(self) -> tuple[int, dict]:
        """Return discovered video projects for the configured project location."""
        settings = self.settings_handler.get_settings()
        project_location = str(settings.get("project_location", "")).strip()
        location_status = str(settings.get("location_status", "unknown"))
        if location_status in {"missing", "unwritable"}:
            return 422, {
                "error": f"project_location_{location_status}",
                "message": f"Configured project location {project_location} is {location_status}.",
                "location_status": location_status,
                "recovery_action": "navigate_to_settings",
            }

        projects = self.project_service.discover_projects(project_location)
        return 200, {
            "project_location": project_location,
            "location_status": location_status,
            "projects": projects,
        }

    def get_projects_detail(self, project_id: str) -> tuple[int, dict]:
        """Return details for one discovered project by project_id."""
        settings = self.settings_handler.get_settings()
        project_location = str(settings.get("project_location", "")).strip()
        project = self.project_service.get_project_detail(project_location, project_id)
        if project is None:
            return 404, {"error": "project_not_found", "message": f"Project {project_id} not found."}
        return 200, project
