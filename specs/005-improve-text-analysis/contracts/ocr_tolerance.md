# Contract: Joined-Only Boundary Matching with Global Tolerance

**File**: `src/services/ocr_service.py`  
**Interfaces**: `_find_in_text(...)`, `extract_with_boundaries(...)`, `evaluate_lines(...)` (joined-only adaptation)

## Purpose

Apply fuzzy boundary matching to joined region text using one global tolerance while enforcing precision guardrails.

## Inputs

- `joined_text: str` (canonical normalized text for region)
- `before_text: str | None`
- `after_text: str | None`
- `tolerance_threshold: float` in [0.60, 0.95]

## Output

- Accepted candidate tuple `(name, matched_pattern_id)` or rejection with reason.

## Mandatory Guardrails

1. Matching runs on joined text only (no standalone per-line path).
2. Candidate span must be nearest valid span.
3. Candidate span must contain at most 6 whitespace-delimited tokens between matched boundaries.
4. Extracted token must be non-empty after normalization.
5. Extracted token must include at least one alphanumeric character.

## Tolerance Semantics

- 0.75 default strict behavior.
- Lower values increase tolerance to OCR character substitutions.
- Values outside range must be clamped or rejected at configuration boundary.

## Performance Expectations

- Fuzzy search remains O(m * n) worst-case per boundary probe.
- Guardrails reduce false-positive escalation in long joined strings.

