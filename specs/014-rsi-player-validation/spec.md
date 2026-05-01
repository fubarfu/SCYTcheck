# Feature Specification: RSI Player Validation Signal

**Feature Branch**: `014-add-rsi-player-validation`  
**Created**: 2026-05-01  
**Status**: Draft  
**Input**: User description: "During analysis identified names shall be checked against the webpage of the game https://robertsspaceindustries.com/en/citizens/<PlayerName> ..."

> For web UI features, the feature specification defines required behavior and user outcomes.
> Google Stitch remains authoritative for UI design decisions unless the spec explicitly
> overrides a design point.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Candidates During Analysis (Priority: P1)

As an analyst, I want detected player-name candidates to be verified against the official citizen profile page so recommendation confidence is strongly influenced by whether a real player record exists.

**Why this priority**: This creates the primary value of the feature by separating likely real player names from OCR noise and directly improving analysis recommendations.

**Independent Test**: Run analysis with validation enabled on a video that yields repeated and unique candidate spellings; confirm each unique spelling is validated once per run and recommendation strength reflects found vs not found outcomes.

**Acceptance Scenarios**:

1. **Given** analysis validation is enabled and analysis detects candidate spellings, **When** the scan completes, **Then** results are immediately available; each candidate shows its current validation state (found, not found, checking, or failed), with pending validations updating in real-time as queue requests complete.
2. **Given** analysis validation is enabled and the same spelling appears multiple times, **When** analysis runs, **Then** that spelling is checked at most once during that run and reused for all matching candidates.
3. **Given** both found and not-found candidate outcomes exist, **When** recommendations are calculated, **Then** found outcomes receive a substantially stronger recommendation signal than not-found outcomes.

---

### User Story 2 - Control Validation in Analysis Settings (Priority: P2)

As a user, I want a settings option to disable external player validation so I can run analysis without performing website checks.

**Why this priority**: Users need control over network behavior and runtime trade-offs while keeping the rest of analysis workflow intact.

**Independent Test**: Turn validation off in analysis settings, run analysis, and confirm no external validation checks occur while other analysis outputs still generate normally.

**Acceptance Scenarios**:

1. **Given** the user disables validation in analysis settings, **When** analysis runs, **Then** no player-profile validation requests are made.
2. **Given** validation is disabled, **When** results are shown, **Then** candidates show a neutral or unavailable validation state instead of found/not-found.

---

### User Story 3 - Recheck Individual Candidates in Review (Priority: P3)

As a reviewer, I want to trigger a one-off validation check for an individual candidate card, including manually edited names, so I can verify uncertain cases without rerunning full analysis.

**Why this priority**: Manual recheck supports correction workflows and preserves value when candidate names are edited during review.

**Independent Test**: Open review, edit a candidate spelling, trigger individual check, and confirm the returned found/not-found status and icon update only for that candidate.

**Acceptance Scenarios**:

1. **Given** a candidate in review has any current validation state, **When** the reviewer triggers an individual check, **Then** the candidate is revalidated using its current displayed spelling.
2. **Given** a reviewer edits a candidate name, **When** they trigger individual check, **Then** the check uses the edited spelling and updates the candidate icon based on the result.
3. **Given** an individual check cannot complete, **When** the attempt finishes, **Then** the UI shows a non-blocking failure state and leaves the candidate reviewable.

---

### Edge Cases

- **Site unavailable / unexpected response**: HTTP 200 = found; HTTP 404 = not found; any other status code (5xx, timeout, network error, unexpected redirect) = failed/unavailable state. A request that does not complete within 10 seconds is treated as a timeout failure. The system does not inspect response body content.
- **How does the system handle special characters, whitespace variants, and mixed-case spellings?**: Deduplication normalizes by lowercasing and stripping leading/trailing whitespace only. Internal whitespace variants and special characters are preserved as-is and treated as distinct spellings.
- **Many unique spellings discovered quickly**: New candidates are enqueued for validation immediately upon discovery; the queue dispatches at a maximum rate of one request per second. If the scan completes while requests are still in-flight or queued, those requests continue until the queue drains. Results are accessible immediately after scan completion; pending candidates show a "checking" state and update live.
- **Repeated individual rechecks in short succession**: While a manual recheck is in-flight for a candidate, the Re-check button for that candidate is disabled. It re-enables when the in-flight check reaches a terminal state (found/not_found/failed). This prevents race conditions between concurrent manual checks for the same candidate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support optional candidate validation against `https://robertsspaceindustries.com/en/citizens/<PlayerName>`. Detection is HTTP-status-based: HTTP 200 = found, HTTP 404 = not found, any other status = failed/unavailable. Response body content is not inspected.
- **FR-002**: When validation is enabled, the system MUST determine and store a found/not-found outcome for each unique candidate spelling detected during an analysis run.
- **FR-003**: During a single analysis run, the system MUST check each unique candidate spelling no more than once.
- **FR-003a**: Validation requests MUST be dispatched concurrently with video scanning and OCR — a new unique spelling MUST be enqueued for validation as soon as it is first discovered, without waiting for the full scan to complete.
- **FR-003b**: When the video scan completes, results MUST be immediately accessible. Candidates with in-flight or queued validation requests MUST show a "checking" state and update their icon in real-time as each request resolves, without requiring the user to wait.
- **FR-004**: Validation outcomes MUST strongly influence recommendation strength, with found outcomes weighted substantially higher than not-found outcomes.
- **FR-005**: Analysis settings MUST provide a user-controlled toggle to enable or disable external validation.
- **FR-006**: When validation is disabled, the system MUST perform zero external validation requests during analysis.
- **FR-007**: The system MUST avoid request patterns that resemble abusive traffic and MUST pace consecutive outbound validation requests to a minimum of 1 second apart. Requests are dispatched from a queue as candidates are discovered during scanning; pacing applies to the queue dispatch rate, not to when candidates are discovered. Each individual request MUST have a timeout of 10 seconds; exceeding this timeout results in a failed/unavailable state for that candidate.
- **FR-008**: The review view MUST display an icon on each candidate card that reflects validation state (found, not found, checking/pending, unavailable, or failed).
- **FR-009**: The review view MUST allow a reviewer to trigger an individual validation check for a specific candidate.
- **FR-010**: Individual validation checks in review MUST use the candidate spelling currently shown in the card, including manual edits. The client MUST include the current displayed spelling in the recheck request body; the backend validates against the provided spelling and persists it to the sidecar. The sidecar spelling is not used as the source during a manual recheck to avoid stale-name bugs when a candidate has been edited but the sidecar has not yet been flushed.
- **FR-011**: An individual validation check MUST update only the targeted candidate card state and must not block review of other candidates.
- **FR-012**: If a validation attempt fails, the system MUST preserve reviewer progress and present a clear non-blocking status.
- **FR-013**: Validation outcomes MUST persist with the analysis/review state for the current result so users can reopen and continue review without losing prior results. Outcomes are NOT shared or reused across separate analysis runs.
- **FR-014**: The system MUST clearly distinguish between not-found results and unattempted/disabled validation states.

### Key Entities *(include if feature involves data)*

- **Candidate Validation Record**: Validation state associated with a candidate spelling or reviewed candidate; includes checked name, outcome, last checked time, and result source (analysis batch vs manual review check).
- **Validation Preference**: User-controlled analysis setting that enables or disables automatic external validation during analysis.
- **Recommendation Signal**: Scoring input that combines existing analysis evidence with validation outcome to produce recommendation strength.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With validation enabled, 100% of unique candidate spellings detected in a run receive either a found or not-found outcome unless an external failure occurs.
- **SC-002**: Duplicate spelling checks are eliminated within each run, resulting in at most one external check per unique spelling.
- **SC-003**: With validation disabled, analysis performs zero external validation requests.
- **SC-004**: External validation traffic remains bounded so that consecutive outbound requests are spaced at least 1 second apart for the entire run.
- **SC-005**: In review, 95% of individual manual checks update the candidate icon to a terminal state (found/not-found/failed) within 5 seconds under normal connectivity.
- **SC-006**: Recommendation ordering reflects validation signal such that found candidates are consistently ranked above otherwise equivalent not-found candidates.
- **SC-007**: Reviewers can identify validation state directly from candidate cards without opening additional detail views.

## Assumptions

- The citizen profile page can be accessed publicly without user authentication.
- Website availability and response consistency are outside user control, so transient failures are expected and must be handled gracefully.
- Existing recommendation logic can accept an additional weighted signal without changing the broader review workflow.
- Candidate spelling comparison for one-time checks uses lowercase + strip leading/trailing whitespace normalization within a run (e.g., `PlayerName` and `playername` are treated as the same spelling).
- Validation outcomes are scoped to a single analysis run and its associated review state; results from prior runs are not reused as a cache for subsequent runs.
- This feature does not require bulk historical backfill; validation applies to newly analyzed or manually rechecked candidates.

## Clarifications

### Session 2026-05-01

- Q: How does the system determine whether a citizen profile exists (found vs not-found)? → A: HTTP status only — 200 = found, 404 = not found, any other status = failed/unavailable; response body is not inspected.
- Q: What is the minimum delay between consecutive outbound validation requests during a batch analysis run? → A: 1 second between requests.
- Q: Do validation outcomes persist across sessions for reuse in subsequent runs? → A: Run-scoped only; each analysis run checks fresh, no result is reused across runs.
- Q: What normalization is applied to candidate spellings for within-run deduplication? → A: Lowercase + strip leading/trailing whitespace only.
- Q: What HTTP request timeout triggers the failed/unavailable state? → A: 10 seconds.
- Constraint: Validation checks MUST start concurrently with video scanning and OCR; spellings are enqueued for checking as discovered, queue dispatches at 1 req/sec, continues draining after scan completes.
- Q: When scan completes with validation still pending, can user access results? → A: Yes — results available immediately; pending candidates show "checking" state and update live as requests complete.