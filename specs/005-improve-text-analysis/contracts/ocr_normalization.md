# Contract: Joined Region Text Normalization

**File**: `src/services/ocr_service.py`  
**Interfaces**: `normalize_for_matching(text: str) -> str`, `build_joined_region_text(lines: list[str]) -> str`

## Purpose

Provide the canonical joined text input for joined-only context-pattern matching.

## Inputs

- `lines: list[str]` from OCR for one frame-region pair.
- `text: str` for low-level normalization helper.

## Output

- Single normalized string with no newline characters and collapsed whitespace.

## Rules

1. Remove empty lines after stripping.
2. Join retained lines in OCR order using a single space.
3. Normalize with whitespace collapsing.
4. Return empty string if all inputs are empty.

## Determinism and Complexity

- Deterministic and side-effect-free.
- O(n) time where n is total character count.

## Invariants

- `"\n" not in joined_text`
- `joined_text == normalize_for_matching(joined_text)`

