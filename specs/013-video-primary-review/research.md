# Research: Video-Primary Review Flow

**Feature**: 013-video-primary-review  
**Date**: 2026-04-28  
**Status**: Complete  

## Overview

All critical design questions were clarified during the specification phase through five targeted clarification cycles (`/speckit.clarify`). No blocking technical unknowns remain.

---

## Clarifications Resolved

### 1. Project Discovery Source
**Question**: Should the Videos view keep using an app-level history record to track projects?  
**Decision**: No. Projects are derived directly from the configured project location; no separate app-level history is retained.  
**Rationale**: Simplifies project state management. Filesystem becomes the single source of truth. Eliminates stale history data.  
**Implementation Impact**: `history_service.py` modified to scan filesystem directly instead of maintaining app-level project list.

### 2. Project Location Initialization
**Question**: Must the user define a project location before first use?  
**Decision**: No. A default project location is defined in app-level settings and used automatically on first run.  
**Rationale**: Reduces friction on first launch. Users can later change it via Settings.  
**Implementation Impact**: `config.py` must set sensible default (e.g., `~/Videos/SCYTcheck` or `%APPDATA%/SCYTcheck/projects`).

### 3. Merged Review Conflict Resolution
**Question**: How should merged review conflicts be resolved when a prior reviewed decision conflicts with a newly analyzed result?  
**Decision**: Prior human-reviewed status wins; the new run adds evidence but does not override reviewed decisions automatically.  
**Rationale**: Preserves user trust. Human judgment is authoritative once exercised.  
**Implementation Impact**: `review_service.py` must implement conflict resolution: `prior_decision OR new_analysis_evidence`.

### 4. Candidate Freshness Duration
**Question**: How long should a candidate remain marked as new?  
**Decision**: Keep new until the user explicitly confirms, rejects, or edits that candidate.  
**Rationale**: Users need persistent indication of newly discovered items.  
**Implementation Impact**: Freshness flag persists across review session; cleared only on user action.

### 5. Candidate Freshness Trigger
**Question**: Which candidates qualify for a new marker?  
**Decision**: Only candidates whose spelling differs from previously existing candidates qualify as new.  
**Rationale**: Avoids false positives from duplicate detection of same misspelling.  
**Implementation Impact**: Freshness algorithm: `new_spelling NOT IN (all_prior_spellings_for_video)`.

### 6. Progress Messaging & Auto-Open
**Question**: What should users see in the progress window regarding project status? Should review open automatically?  
**Decision**: The progress window shall show whether a new project is being created or results will be merged with an existing project. Review view opens automatically after analysis completes.  
**Rationale**: Gives users critical context during long-running analysis. Removes manual transition friction.  
**Implementation Impact**:
- Backend: Determine project create vs. merge status before analysis starts; stream messaging during progress.
- Frontend: Consume progress messages; auto-redirect to review on completion signal.

---

## Design Decisions Locked

All design decisions have been captured in the feature spec:
- **Storage**: CSV + JSON sidecar per video (no database)
- **Technology**: Python 3.11 backend, React/TypeScript frontend
- **UI Authority**: Google Stitch (see `specs/013-video-primary-review/stitch/`)
- **Testing**: pytest (backend), vitest (frontend)
- **No new dependencies**: Use existing tech stack

---

## Technical Considerations (Resolved)

### Per-Video Workspace Structure
**Current**: `.scyt_review_workspaces/<video_id>/`  
**Preserved**: All existing per-video storage conventions remain. Phase 1 design respects current structure.

### Video URL Metadata Availability
**Handling**: Assume metadata available for most projects. Fallback to video filename if URL unavailable.  
**Risk**: Minimal (metadata usually present; fallback acceptable per spec).

### Project Location Availability on First Run
**Handling**: If default location unavailable/unwritable, show blocking error with recovery path (e.g., "Please choose a valid project location in Settings").  
**Risk**: Acceptable; users can recover by accessing Settings.

### Multiple Analysis Runs Same Video
**Ordering**: Assume run ordering is deterministic (by timestamp or directory mtime).  
**Merge Logic**: Latest run is "new"; all others are "historical". Candidates from latest run checked for new spelling.

---

## Completion Status

✅ All research inputs satisfied.  
✅ No blocking unknowns remain.  
✅ Ready for Phase 1 (Design & Data Model).

**Next Step**: Execute Phase 1 design via data-model.md, contracts/, quickstart.md, and Google Stitch UI design.
