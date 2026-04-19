<!-- Sync Impact Report
Version change: 1.1.0 → 1.2.0
List of modified principles: Added principle VIII for Google Stitch web UI workflow
Added sections: None
Removed sections: None
Templates requiring updates: None
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

### VIII. Google Stitch for Lean Web UI
For web-based UI features, default to Google Stitch-driven design and generation workflows.

- Use Google Stitch project/screen/design-system tools to define and evolve UI work.
- Prioritize modern, lean interfaces: minimal complexity, clear hierarchy, responsive layouts, and fast loading.
- Keep generated UI consistent with product goals and existing visual language; avoid unnecessary UI bloat.
- Validate that resulting screens are implementation-ready and maintainable in the repository context.

## Additional Constraints
Technology stack requirements, compliance standards, deployment policies, etc.

Web UI delivery constraint: when a task includes creating or substantially redesigning web UI, Google Stitch is the primary design/generation path unless explicitly overridden by feature requirements.

## Development Workflow
Code review requirements, testing gates, deployment approval process, etc.

## Governance
Constitution supersedes all other practices; Amendments require documentation, approval, migration plan

All PRs/reviews must verify compliance; Complexity must be justified; Use constitution.md for runtime development guidance

**Version**: 1.2.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-19
