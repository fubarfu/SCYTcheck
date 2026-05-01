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

1. **Given** analysis validation is enabled and analysis detects candidate spellings, **When** the run completes, **Then** each unique candidate spelling includes a registry-check outcome of found or not found.
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

- What happens when the external citizen page is temporarily unavailable or returns an unexpected response format?
- How does the system handle special characters, whitespace variants, and mixed-case spellings when determining whether two candidates are the same spelling for one-time checks?
- What happens if many unique candidate spellings are discovered quickly in one run?
- How does review behave when a user triggers repeated individual checks for the same candidate in a short period?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support optional candidate validation against `https://robertsspaceindustries.com/en/citizens/<PlayerName>`.
- **FR-002**: When validation is enabled, the system MUST determine and store a found/not-found outcome for each unique candidate spelling detected during an analysis run.
- **FR-003**: During a single analysis run, the system MUST check each unique candidate spelling no more than once.
- **FR-004**: Validation outcomes MUST strongly influence recommendation strength, with found outcomes weighted substantially higher than not-found outcomes.
- **FR-005**: Analysis settings MUST provide a user-controlled toggle to enable or disable external validation.
- **FR-006**: When validation is disabled, the system MUST perform zero external validation requests during analysis.
- **FR-007**: The system MUST avoid request patterns that resemble abusive traffic and MUST pace validation checks to remain respectful to the external website.
- **FR-008**: The review view MUST display an icon on each candidate card that reflects validation state (found, not found, unavailable, or failed).
- **FR-009**: The review view MUST allow a reviewer to trigger an individual validation check for a specific candidate.
- **FR-010**: Individual validation checks in review MUST use the candidate spelling currently shown in the card, including manual edits.
- **FR-011**: An individual validation check MUST update only the targeted candidate card state and must not block review of other candidates.
- **FR-012**: If a validation attempt fails, the system MUST preserve reviewer progress and present a clear non-blocking status.
- **FR-013**: Validation outcomes MUST persist with analysis/review state so users can reopen and continue review without losing prior results.
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
- **SC-004**: External validation traffic remains bounded so that request pacing stays within configured safe limits for the entire run.
- **SC-005**: In review, 95% of individual manual checks update the candidate icon to a terminal state (found/not-found/failed) within 5 seconds under normal connectivity.
- **SC-006**: Recommendation ordering reflects validation signal such that found candidates are consistently ranked above otherwise equivalent not-found candidates.
- **SC-007**: Reviewers can identify validation state directly from candidate cards without opening additional detail views.

## Assumptions

- The citizen profile page can be accessed publicly without user authentication.
- Website availability and response consistency are outside user control, so transient failures are expected and must be handled gracefully.
- Existing recommendation logic can accept an additional weighted signal without changing the broader review workflow.
- Candidate spelling comparison for one-time checks uses a consistent normalization rule within a run.
- This feature does not require bulk historical backfill; validation applies to newly analyzed or manually rechecked candidates.