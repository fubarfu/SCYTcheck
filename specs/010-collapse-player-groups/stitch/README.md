# Stitch Artifacts for Feature 010

These files are the local authoritative reference snapshots for the review-group UI states used by feature 010:

- `review-candidate-groups.html`: mixed consensus/conflict group listing.
- `review-validation-error-state.html`: duplicate-name validation feedback state.
- `review-expanded-candidate-group.html`: expanded group with selection/reject controls.

Notes:
- These artifacts are static references for implementation and QA alignment.
- Runtime behavior is implemented in `src/web/frontend/src/pages/ReviewPage.tsx` and related components.
- Any approved visual deviations must be documented in this file and in `specs/010-collapse-player-groups/quickstart.md`.
