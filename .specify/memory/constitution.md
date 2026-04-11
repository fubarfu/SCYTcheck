<!-- Sync Impact Report
Version change: 1.0.0 → 1.1.0
List of modified principles: All principles updated to reflect maintainable VS Code-friendly application rules
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

## Additional Constraints
Technology stack requirements, compliance standards, deployment policies, etc.

## Development Workflow
Code review requirements, testing gates, deployment approval process, etc.

## Governance
Constitution supersedes all other practices; Amendments require documentation, approval, migration plan

All PRs/reviews must verify compliance; Complexity must be justified; Use constitution.md for runtime development guidance

**Version**: 1.1.0 | **Ratified**: 2026-04-11 | **Last Amended**: 2026-04-11
