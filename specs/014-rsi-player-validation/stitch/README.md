# Stitch Screens — Feature 014: RSI Player Validation

Stitch project: **SCYTcheck Web UI** (project ID `1293475510601425942`)

## Screens

### 1. Review - Expanded Candidate Group (with Validation States)
- **Screen ID**: `2b3b3615129a4879ba1e0748e52aac38`
- **HTML**: [review-expanded-candidate-group-validation-states.html](./review-expanded-candidate-group-validation-states.html)
- **Screenshot**: [review-expanded-candidate-group-validation-states.png](./review-expanded-candidate-group-validation-states.png)
- **Description**: Candidate card rows extended with RSI validation state icons and Re-check buttons.
  - `found` → green `check_circle` icon + "Re-check" text button
  - `not_found` → amber `person_off` icon + "Re-check" text button
  - `checking` → grey animated `progress_activity` spinner; Re-check hidden
  - `failed` → red `error_outline` icon + "Re-check" text button
  - `unchecked` → no icon

### 2. Analysis View (with Validation Toggle)
- **Screen ID**: `0576734766574b979811eadd1978f86c`
- **HTML**: [analysis-view-validation-toggle.html](./analysis-view-validation-toggle.html)
- **Screenshot**: [analysis-view-validation-toggle.png](./analysis-view-validation-toggle.png)
- **Description**: Analysis settings panel with a new "Validate player names (RSI)" toggle added after the Matching Tolerance row.
  - Primary label: "Validate player names"
  - Subtitle: "Checks detected names against robertsspaceindustries.com during analysis (1 req/sec)"
  - Toggle shown in ON/enabled (blue) state

## Design System
- Dark mode, primary blue `#3B82F6`
- Fonts: Plus Jakarta Sans (headline), Inter (body/label)
- Roundness: ROUND_FOUR
- Device: DESKTOP (2560px wide)
