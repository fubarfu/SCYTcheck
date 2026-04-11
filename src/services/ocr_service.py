from __future__ import annotations

import re

import cv2
import numpy as np
import pytesseract
from thefuzz import fuzz as _fuzz

from src.data.models import ContextPattern


class OCRError(RuntimeError):
    pass


class PatternValidationError(ValueError):
    pass


class OCRService:
    def __init__(self, confidence_threshold: int = 40, tesseract_cmd: str | None = None) -> None:
        self.confidence_threshold = confidence_threshold
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    def detect_text(self, image: np.ndarray, region: tuple[int, int, int, int]) -> list[str]:
        tokens, _ = self.detect_text_with_diagnostics(image, region)
        return tokens

    def detect_text_with_diagnostics(
        self,
        image: np.ndarray,
        region: tuple[int, int, int, int],
    ) -> tuple[list[str], list[dict[str, object]]]:
        x, y, width, height = region
        cropped = image[y : y + height, x : x + width]
        if cropped.size == 0:
            return [], [
                {
                    "raw_string": "",
                    "accepted": False,
                    "rejection_reason": "empty_crop",
                    "extracted_name": "",
                    "matched_pattern": None,
                }
            ]

        preprocessed = self.preprocess_image(cropped)

        try:
            data = pytesseract.image_to_data(
                preprocessed,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",
            )
        except Exception as exc:  # pragma: no cover - pytesseract failures are environment-specific
            raise OCRError(str(exc)) from exc

        tokens: list[str] = []
        diagnostics: list[dict[str, object]] = []
        line_entries = self._build_line_entries(data)

        for line_text, avg_conf in line_entries:
            norm = OCRService.normalize_for_matching(line_text)
            if avg_conf >= self.confidence_threshold:
                tokens.append(line_text)
                diagnostics.append(
                    {
                        "raw_string": line_text,
                        "tested_string_raw": line_text,
                        "tested_string_normalized": norm,
                        "accepted": True,
                        "rejection_reason": "",
                        "extracted_name": line_text,
                        "matched_pattern": None,
                    }
                )
            else:
                diagnostics.append(
                    {
                        "raw_string": line_text,
                        "tested_string_raw": line_text,
                        "tested_string_normalized": norm,
                        "accepted": False,
                        "rejection_reason": "low_confidence",
                        "extracted_name": "",
                        "matched_pattern": None,
                    }
                )

        if not line_entries:
            diagnostics.append(
                {
                    "raw_string": "",
                    "tested_string_raw": "",
                    "tested_string_normalized": "",
                    "accepted": False,
                    "rejection_reason": "no_ocr_output",
                    "extracted_name": "",
                    "matched_pattern": None,
                }
            )

        return tokens, diagnostics

    @staticmethod
    def _build_line_entries(data: dict[str, object]) -> list[tuple[str, int]]:
        """Build OCR line strings with average confidence.

        Prefer grouping by Tesseract line metadata when available. If line metadata is
        missing, fall back to token-level entries to preserve current behavior in tests
        and simplified OCR outputs.
        """
        texts = list(data.get("text", []) if isinstance(data, dict) else [])
        confs = list(data.get("conf", []) if isinstance(data, dict) else [])
        block_nums = data.get("block_num")
        par_nums = data.get("par_num")
        line_nums = data.get("line_num")

        line_meta_available = isinstance(block_nums, list) and isinstance(par_nums, list) and isinstance(line_nums, list)

        def parse_conf(raw: object) -> int:
            try:
                return int(float(str(raw)))
            except ValueError:
                return 0

        if line_meta_available:
            grouped: dict[tuple[int, int, int], list[tuple[int, str, int]]] = {}
            for index, text in enumerate(texts):
                value = str(text).strip()
                if not value:
                    continue
                try:
                    key = (
                        int(block_nums[index]),
                        int(par_nums[index]),
                        int(line_nums[index]),
                    )
                except (IndexError, TypeError, ValueError):
                    # If metadata is inconsistent, fall back to token-level output.
                    line_meta_available = False
                    break
                conf = parse_conf(confs[index] if index < len(confs) else "0")
                grouped.setdefault(key, []).append((index, value, conf))

            if line_meta_available:
                lines: list[tuple[str, int]] = []
                for key in sorted(grouped.keys()):
                    ordered_tokens = sorted(grouped[key], key=lambda item: item[0])
                    line_text = " ".join(token for _, token, _ in ordered_tokens).strip()
                    if not line_text:
                        continue
                    avg_conf = int(round(sum(conf for _, _, conf in ordered_tokens) / len(ordered_tokens)))
                    lines.append((line_text, avg_conf))
                return lines

        fallback_lines: list[tuple[str, int]] = []
        for index, text in enumerate(texts):
            value = str(text).strip()
            if not value:
                continue
            conf = parse_conf(confs[index] if index < len(confs) else "0")
            fallback_lines.append((value, conf))
        return fallback_lines

    @staticmethod
    def validate_pattern(before_text: str | None, after_text: str | None) -> None:
        """Ensure pattern has at least one boundary token configured."""
        if not (before_text and before_text.strip()) and not (after_text and after_text.strip()):
            raise PatternValidationError("Pattern must define before_text and/or after_text.")

    @staticmethod
    def normalize_for_matching(text: str) -> str:
        """Normalize OCR text for pattern matching: remove newlines, collapse whitespace."""
        text = (text or "").replace("\n", " ").replace("\r", " ")
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _find_in_text(
        pattern: str,
        text: str,
        threshold: float = 0.75,
    ) -> tuple[int, int] | None:
        """Locate pattern in text: exact match first, then fuzzy scan, then boundary-clipped.

        Returns (start, end) char positions within text, or None if not found at threshold.
        """
        if not pattern or not text:
            return None

        p_lower = pattern.lower()
        t_lower = text.lower()
        p_len = len(p_lower)
        t_len = len(t_lower)

        # 1. Exact case-insensitive substring match.
        pos = t_lower.find(p_lower)
        if pos >= 0:
            return pos, pos + p_len

        # 2. Fuzzy sliding-window scan.
        if p_len <= t_len:
            best_score = 0.0
            best_pos = -1
            for i in range(t_len - p_len + 1):
                window = t_lower[i : i + p_len]
                score = _fuzz.ratio(p_lower, window) / 100.0
                if score > best_score:
                    best_score = score
                    best_pos = i
            if best_score >= threshold:
                return best_pos, best_pos + p_len

        # 3. Boundary-clipped: ≥2 contiguous chars of pattern overlap at OCR region edge.
        if p_len >= 2:
            # Pattern's tail at the start of OCR text (region clipped pattern's beginning).
            for overlap in range(p_len, 1, -1):
                if t_lower.startswith(p_lower[-overlap:]):
                    return 0, overlap
            # Pattern's head at the end of OCR text (region clipped pattern's end).
            for overlap in range(p_len, 1, -1):
                if t_lower.endswith(p_lower[:overlap]):
                    return t_len - overlap, t_len

        return None

    @staticmethod
    def extract_with_boundaries(
        line: str,
        before_text: str | None = None,
        after_text: str | None = None,
        threshold: float = 0.75,
    ) -> str | None:
        """Extract single player-name token using before/after/both boundary rules."""
        result = OCRService._extract_with_boundaries_meta(
            line, before_text=before_text, after_text=after_text, threshold=threshold
        )
        return result[0] if result else None

    @staticmethod
    def _extract_with_boundaries_meta(
        line: str,
        before_text: str | None = None,
        after_text: str | None = None,
        threshold: float = 0.75,
    ) -> tuple[str, int, int] | None:
        """Find marker positions fuzzily and extract single player-name token.

        Returns (token, name_start_pos, full_span_len) for tie-break purposes,
        where full_span_len is the pre-tokenisation span to preserve tie-break
        correctness, or None if no match.
        """
        OCRService.validate_pattern(before_text, after_text)
        norm = OCRService.normalize_for_matching(line)
        before = before_text.strip() if before_text else None
        after = after_text.strip() if after_text else None

        if before and after:
            b_range = OCRService._find_in_text(before, norm, threshold)
            if not b_range:
                return None
            remaining = norm[b_range[1]:]
            a_range = OCRService._find_in_text(after, remaining, threshold)
            if not a_range:
                return None
            span_text = remaining[: a_range[0]].strip()
            if not span_text:
                return None
            tokens = span_text.split()
            token = tokens[0] if tokens else ""  # both-boundary: first token between markers
            if not token:
                return None
            return token, b_range[1], len(span_text)

        if before:
            b_range = OCRService._find_in_text(before, norm, threshold)
            if not b_range:
                return None
            span_text = norm[b_range[1] :].strip()
            if not span_text:
                return None
            tokens = span_text.split()
            token = tokens[0] if tokens else ""  # before-only: first token after marker
            if not token:
                return None
            return token, b_range[1], len(span_text)

        # after-only
        a_range = OCRService._find_in_text(after or "", norm, threshold)
        if not a_range:
            return None
        span_text = norm[: a_range[0]].strip()
        if not span_text:
            return None
        tokens = span_text.split()
        token = tokens[-1] if tokens else ""  # after-only: last token before marker
        if not token:
            return None
        return token, 0, len(span_text)

    def extract_candidates(
        self,
        lines: list[str],
        patterns: list[ContextPattern] | None = None,
        filter_non_matching: bool = False,
    ) -> list[tuple[str, str | None]]:
        """Extract candidate names from OCR lines using optional context patterns.

        Returns tuples of (candidate_name, matched_pattern_id).
        """
        decisions = self.evaluate_lines(
            lines,
            patterns=patterns,
            filter_non_matching=filter_non_matching,
        )
        return [
            (str(decision["extracted_name"]), decision["matched_pattern"])
            for decision in decisions
            if bool(decision["accepted"])
        ]

    def evaluate_lines(
        self,
        lines: list[str],
        patterns: list[ContextPattern] | None = None,
        filter_non_matching: bool = False,
    ) -> list[dict[str, object]]:
        """Evaluate OCR lines and return accept/reject decisions with reasons.

        Each decision includes: raw_string, tested_string_raw, tested_string_normalized,
        accepted, rejection_reason, extracted_name, matched_pattern.
        """
        active_patterns = [pattern for pattern in (patterns or []) if pattern.enabled]
        decisions: list[dict[str, object]] = []

        for line in lines:
            source = (line or "").strip()
            if not source:
                continue

            tested_normalized = OCRService.normalize_for_matching(source)

            matched_candidates: list[tuple[str, str, int, int, int]] = []
            for pattern_index, pattern in enumerate(active_patterns):
                threshold = getattr(pattern, "similarity_threshold", 0.75)
                try:
                    meta = self._extract_with_boundaries_meta(
                        source,
                        before_text=pattern.before_text,
                        after_text=pattern.after_text,
                        threshold=threshold,
                    )
                except PatternValidationError:
                    continue

                if meta:
                    extracted, start_pos, span_len = meta
                    matched_candidates.append(
                        (extracted, pattern.id, span_len, start_pos, pattern_index)
                    )

            if matched_candidates:
                # Deterministic conflict resolution:
                # longest span, then earliest start, then pattern order.
                selected = sorted(
                    matched_candidates, key=lambda item: (-item[2], item[3], item[4])
                )[0]
                extracted_name = selected[0].strip()
                decisions.append(
                    {
                        "raw_string": source,
                        "tested_string_raw": source,
                        "tested_string_normalized": tested_normalized,
                        "accepted": True,
                        "rejection_reason": "",
                        "extracted_name": extracted_name,
                        "matched_pattern": selected[1],
                    }
                )
            elif not filter_non_matching:
                decisions.append(
                    {
                        "raw_string": source,
                        "tested_string_raw": source,
                        "tested_string_normalized": tested_normalized,
                        "accepted": True,
                        "rejection_reason": "",
                        "extracted_name": source,
                        "matched_pattern": None,
                    }
                )
            else:
                decisions.append(
                    {
                        "raw_string": source,
                        "tested_string_raw": source,
                        "tested_string_normalized": tested_normalized,
                        "accepted": False,
                        "rejection_reason": "no_pattern_match",
                        "extracted_name": "",
                        "matched_pattern": None,
                    }
                )

        return decisions
