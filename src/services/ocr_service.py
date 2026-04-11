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
        x, y, width, height = region
        cropped = image[y : y + height, x : x + width]
        if cropped.size == 0:
            return []

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
        for index, text in enumerate(data.get("text", [])):
            value = text.strip()
            if not value:
                continue
            conf_raw = data.get("conf", ["0"])[index]
            try:
                conf = int(float(conf_raw))
            except ValueError:
                conf = 0
            if conf >= self.confidence_threshold:
                tokens.append(value)

        return tokens

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

    def extract_candidates(
        self,
        lines: list[str],
        patterns: list[ContextPattern] | None = None,
        filter_non_matching: bool = False,
    ) -> list[tuple[str, str | None]]:
        """Extract candidate names from OCR lines using optional context patterns.

        Returns tuples of (candidate_name, matched_pattern_id).
        """
        candidates: list[tuple[str, str | None]] = []
        active_patterns = [pattern for pattern in (patterns or []) if pattern.enabled]

        for line in lines:
            source = (line or "").strip()
            if not source:
                continue

            matched_any = False
            for pattern in active_patterns:
                try:
                    extracted = self.extract_with_boundaries(
                        source,
                        before_text=pattern.before_text,
                        after_text=pattern.after_text,
                    )
                except PatternValidationError:
                    continue

                if extracted:
                    candidates.append((extracted, pattern.id))
                    matched_any = True

            if not matched_any and not filter_non_matching:
                candidates.append((source, None))

        return candidates
