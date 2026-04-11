from __future__ import annotations

import re

import cv2
import numpy as np
import pytesseract

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
        saw_non_empty = False
        for index, text in enumerate(data.get("text", [])):
            value = text.strip()
            if not value:
                continue
            saw_non_empty = True
            conf_raw = data.get("conf", ["0"])[index]
            try:
                conf = int(float(conf_raw))
            except ValueError:
                conf = 0
            if conf >= self.confidence_threshold:
                tokens.append(value)
                diagnostics.append(
                    {
                        "raw_string": value,
                        "accepted": True,
                        "rejection_reason": "",
                        "extracted_name": value,
                        "matched_pattern": None,
                    }
                )
            else:
                diagnostics.append(
                    {
                        "raw_string": value,
                        "accepted": False,
                        "rejection_reason": "low_confidence",
                        "extracted_name": "",
                        "matched_pattern": None,
                    }
                )

        if not saw_non_empty:
            diagnostics.append(
                {
                    "raw_string": "",
                    "accepted": False,
                    "rejection_reason": "no_ocr_output",
                    "extracted_name": "",
                    "matched_pattern": None,
                }
            )

        return tokens, diagnostics

    @staticmethod
    def validate_pattern(before_text: str | None, after_text: str | None) -> None:
        """Ensure pattern has at least one boundary token configured."""
        if not (before_text and before_text.strip()) and not (after_text and after_text.strip()):
            raise PatternValidationError("Pattern must define before_text and/or after_text.")

    @staticmethod
    def extract_with_boundaries(
        line: str,
        before_text: str | None = None,
        after_text: str | None = None,
    ) -> str | None:
        """Extract name from an OCR line using before/after/both boundary rules."""
        OCRService.validate_pattern(before_text, after_text)
        source = line or ""

        before = before_text.strip() if before_text else None
        after = after_text.strip() if after_text else None

        if before and after:
            pattern = rf"{re.escape(before)}\s*(.*?)\s*{re.escape(after)}"
            match = re.search(pattern, source, flags=re.IGNORECASE)
            return match.group(1).strip() if match and match.group(1).strip() else None

        if before:
            pattern = rf"{re.escape(before)}\s*(.*)$"
            match = re.search(pattern, source, flags=re.IGNORECASE)
            return match.group(1).strip() if match and match.group(1).strip() else None

        pattern = rf"^(.*?)\s*{re.escape(after or '')}"
        match = re.search(pattern, source, flags=re.IGNORECASE)
        return match.group(1).strip() if match and match.group(1).strip() else None

    @staticmethod
    def _extract_with_boundaries_meta(
        line: str,
        before_text: str | None = None,
        after_text: str | None = None,
    ) -> tuple[str, int, int] | None:
        OCRService.validate_pattern(before_text, after_text)
        source = line or ""
        before = before_text.strip() if before_text else None
        after = after_text.strip() if after_text else None

        if before and after:
            pattern = rf"{re.escape(before)}\s*(.*?)\s*{re.escape(after)}"
            match = re.search(pattern, source, flags=re.IGNORECASE)
            if not match:
                return None
            extracted = (match.group(1) or "").strip()
            if not extracted:
                return None
            start, end = match.span(1)
            return extracted, start, max(0, end - start)

        if before:
            pattern = rf"{re.escape(before)}\s*(.*)$"
            match = re.search(pattern, source, flags=re.IGNORECASE)
            if not match:
                return None
            extracted = (match.group(1) or "").strip()
            if not extracted:
                return None
            start, end = match.span(1)
            return extracted, start, max(0, end - start)

        pattern = rf"^(.*?)\s*{re.escape(after or '')}"
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            return None
        extracted = (match.group(1) or "").strip()
        if not extracted:
            return None
        start, end = match.span(1)
        return extracted, start, max(0, end - start)

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

        Each decision includes: raw_string, accepted, rejection_reason,
        extracted_name, matched_pattern.
        """
        active_patterns = [pattern for pattern in (patterns or []) if pattern.enabled]
        decisions: list[dict[str, object]] = []

        for line in lines:
            source = (line or "").strip()
            if not source:
                continue

            matched_candidates: list[tuple[str, str, int, int, int]] = []
            for pattern_index, pattern in enumerate(active_patterns):
                try:
                    meta = self._extract_with_boundaries_meta(
                        source,
                        before_text=pattern.before_text,
                        after_text=pattern.after_text,
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
                        "accepted": False,
                        "rejection_reason": "no_pattern_match",
                        "extracted_name": "",
                        "matched_pattern": None,
                    }
                )

        return decisions
