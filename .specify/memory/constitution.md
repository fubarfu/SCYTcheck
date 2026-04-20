<!-- Sync Impact Report
Version change: 1.2.0 → 1.3.0
List of modified principles: VIII. Google Stitch for Lean Web UI → VIII. Google Stitch as UI Design Authority
Added sections: None
Removed sections: None
Templates requiring updates: ✅ .specify/templates/plan-template.md, ✅ .specify/templates/spec-template.md, ✅ .specify/templates/tasks-template.md, ✅ README.md
Follow-up TODOs: None
-->

# SCYTcheck Constitution

## Core Principles

### I. Simple and Modular Architecture

Keep the architecture simple and modular to ensure maintainability and ease of understanding.

### II. Readability Over Cleverness

Prefer readability over cleverness; code should be clear and self-documenting.

### III. Testing for Business Logic

Require tests for non-trivial business logic to ensure reliability and prevent regressions.

### IV. Minimal Dependencies

Keep dependencies minimal to reduce complexity and potential security issues.

### V. No Secrets in Repository

No secrets in the repo; use environment variables or secure vaults for sensitive data.

### VI. Windows-Friendly Development

Ensure Windows-friendly local development with cross-platform compatibility.

### VII. Incremental Changes and Working State

Use small incremental changes and preserve working state to maintain stability.

### VIII. Google Stitch as UI Design Authority

For web-based UI features, Google Stitch MUST be the authoritative source for UI design
direction. Product behavior still belongs in the feature spec, but layout, component
structure, visual hierarchy, and other UI decisions MUST be driven by the current Stitch
project, screens, and design system unless the feature spec explicitly overrides them.

- Use Google Stitch project/screen/design-system tools to define and evolve UI work.
- Consult Stitch whenever a UI decision is required during, planning, implementation, or review.
- Treat approved Stitch screens and design-system assets as the design source of truth for web UI work; implementation MAY adapt only where technical constraints require it, and those deviations MUST be documented.
- Prioritize modern, lean interfaces: minimal complexity, clear hierarchy, responsive layouts, and fast loading.
- Keep generated UI consistent with product goals and existing visual language; avoid unnecessary UI bloat.
- Validate that resulting screens are implementation-ready and maintainable in the repository context.

Rationale: A single authoritative UI source reduces churn between specification,
implementation, and review, and prevents ad hoc design drift in web features.

## Additional Constraints

Technology stack requirements, compliance standards, deployment policies, etc.

Web UI delivery constraint: when a task includes creating or substantially redesigning web
UI, Google Stitch is the primary design/generation path and authoritative design reference
unless explicitly overridden by feature requirements.

## Development Workflow

For web UI features, specification work MUST capture required behavior and user outcomes,
while Stitch artifacts govern UI design decisions. Planning and implementation MUST cite or
consult the active Stitch design whenever UI structure, interaction presentation, or visual
language is decided.

## Governance

Constitution supersedes all other practices. Amendments require documentation, approval,
and a migration plan when workflows or templates must change.

Versioning policy:

- MAJOR for backward-incompatible governance changes or principle removals/redefinitions.
- MINOR for new principles, materially expanded rules, or new mandatory workflow guidance.
- PATCH for clarifications that do not change expected behavior.

Compliance review expectations:

- All PRs and reviews MUST verify constitution compliance.
- Web UI changes MUST verify that the implemented UI matches approved Stitch artifacts, or document justified deviations.
- Complexity must be justified explicitly when a simpler constitution-compliant path is not used.

Use constitution.md as the governing runtime development guidance for the repository.

**Version**: 1.3.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-21
