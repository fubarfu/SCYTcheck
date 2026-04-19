from __future__ import annotations

import re
import ctypes
import os
from importlib import import_module
from pathlib import Path
from tkinter import messagebox

import cv2
import numpy as np
from thefuzz import fuzz as _fuzz

_PADDLEOCR_IMPORT_ERROR: Exception | None = None

try:
    from paddleocr import PaddleOCR
except Exception as exc:  # pragma: no cover - optional dependency in test environments
    PaddleOCR = None  # type: ignore[assignment]
    _PADDLEOCR_IMPORT_ERROR = exc

from src.data.models import ContextPattern


# T018: Precompile whitespace regex for reuse in normalize_for_matching
_RE_WHITESPACE = re.compile(r"\s+")


class OCRError(RuntimeError):
    pass


class PatternValidationError(ValueError):
    pass


class OCRService:
    def __init__(
        self,
        confidence_threshold: int = 40,
        paddleocr_model_root: str | None = None,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.paddleocr_model_root = paddleocr_model_root
        self._ocr_engine: object | None = None

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
            data = self._get_ocr_engine().ocr(preprocessed, cls=False)
        except Exception as exc:
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
    def _build_line_entries(data: object) -> list[tuple[str, int]]:
        """Build OCR line entries from PaddleOCR predictions.

        PaddleOCR returns per-line predictions with confidence in the 0.0..1.0 range.
        This function normalizes confidence to the application's 0..100 scale.
        """

        def to_confidence(value: object) -> int:
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return 0

            if numeric <= 1.0:
                return int(round(max(0.0, min(numeric, 1.0)) * 100.0))
            return int(round(max(0.0, min(numeric, 100.0))))

        if not isinstance(data, list):
            return []

        predictions = data[0] if len(data) == 1 and isinstance(data[0], list) else data
        entries: list[tuple[str, int]] = []

        for item in predictions:
            if not isinstance(item, list | tuple) or len(item) < 2:
                continue
            text_info = item[1]
            if not isinstance(text_info, list | tuple) or len(text_info) < 2:
                continue

            line_text = str(text_info[0]).strip()
            if not line_text:
                continue

            entries.append((line_text, to_confidence(text_info[1])))

        return entries

    def _notify_ocr_initialization_failure(self, message: str) -> None:
        try:
            messagebox.showerror("OCR Initialization Error", message)
        except Exception:
            # UI may not be initialized in tests or CLI execution paths.
            return

    @staticmethod
    def _to_windows_short_path(path_value: str | None) -> str | None:
        if not path_value or os.name != "nt":
            return path_value

        get_short_path_name = getattr(ctypes.windll.kernel32, "GetShortPathNameW", None)
        if get_short_path_name is None:
            return path_value

        input_path = str(Path(path_value))
        required = get_short_path_name(input_path, None, 0)
        if required <= 0:
            return path_value

        buffer = ctypes.create_unicode_buffer(required)
        result = get_short_path_name(input_path, buffer, required)
        if result <= 0:
            return path_value

        short_path = buffer.value
        return short_path or path_value

    def _resolve_model_dirs(self) -> tuple[str | None, str | None, str | None]:
        def resolve_from_root(root: Path) -> tuple[str, str, str] | None:
            if not root.exists() or not root.is_dir():
                return None

            detection_dir: Path | None = None
            recognition_dir: Path | None = None
            classification_dir: Path | None = None

            for child in root.iterdir():
                if not child.is_dir():
                    continue
                name = child.name.lower()
                if detection_dir is None and name.startswith("det"):
                    detection_dir = child
                if classification_dir is None and name.startswith("cls"):
                    classification_dir = child
                if name == "rec_en":
                    recognition_dir = child
                elif recognition_dir is None and name.startswith("rec"):
                    recognition_dir = child

            if not detection_dir or not recognition_dir or not classification_dir:
                return None

            required_files = (
                detection_dir / "inference.pdmodel",
                detection_dir / "inference.pdiparams",
                recognition_dir / "inference.pdmodel",
                recognition_dir / "inference.pdiparams",
                classification_dir / "inference.pdmodel",
                classification_dir / "inference.pdiparams",
            )
            if not all(path.exists() for path in required_files):
                return None

            return str(detection_dir), str(recognition_dir), str(classification_dir)

        candidate_roots: list[Path] = []
        if self.paddleocr_model_root:
            candidate_roots.append(Path(self.paddleocr_model_root))

        try:
            from src import config as app_config

            candidate_roots.extend(app_config._candidate_paddleocr_model_roots())
        except Exception:
            pass

        deduped: list[Path] = []
        seen: set[str] = set()
        for candidate in candidate_roots:
            key = str(candidate.resolve()) if candidate.exists() else str(candidate)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)

        for root in deduped:
            resolved = resolve_from_root(root)
            if resolved:
                self.paddleocr_model_root = str(root)
                return resolved

        checked = ", ".join(str(path) for path in deduped) if deduped else "<none>"
        raise OCRError(
            "PaddleOCR model assets are incomplete. Expected det*, rec*, and cls* "
            "directories each containing inference.pdmodel and inference.pdiparams. "
            f"Checked: {checked}"
        )

    def _create_ocr_engine(self) -> object:
        global PaddleOCR, _PADDLEOCR_IMPORT_ERROR

        if PaddleOCR is None:
            try:
                PaddleOCR = getattr(import_module("paddleocr"), "PaddleOCR")
                _PADDLEOCR_IMPORT_ERROR = None
            except Exception as exc:  # pragma: no cover - runtime init path
                _PADDLEOCR_IMPORT_ERROR = exc

        if PaddleOCR is None:
            details = f" ({_PADDLEOCR_IMPORT_ERROR})" if _PADDLEOCR_IMPORT_ERROR else ""
            raise OCRError(
                "PaddleOCR runtime is not available. Install paddleocr and paddlepaddle "
                "for source runs or ensure the portable bundle includes OCR dependencies."
                f"{details}"
            )

        det_model_dir, rec_model_dir, cls_model_dir = self._resolve_model_dirs()
        kwargs: dict[str, object] = {
            "use_angle_cls": False,
            "lang": "en",
            "use_gpu": False,
            "show_log": False,
        }
        if det_model_dir:
            kwargs["det_model_dir"] = self._to_windows_short_path(det_model_dir)
        if rec_model_dir:
            kwargs["rec_model_dir"] = self._to_windows_short_path(rec_model_dir)
        if cls_model_dir:
            kwargs["cls_model_dir"] = self._to_windows_short_path(cls_model_dir)

        try:
            return PaddleOCR(**kwargs)
        except Exception as exc:  # pragma: no cover - runtime init path
            message = (
                "Failed to initialize PaddleOCR. "
                "Verify bundled OCR assets are available and not blocked."
            )
            self._notify_ocr_initialization_failure(message)
            raise OCRError(f"{message} ({exc})") from exc

    def _get_ocr_engine(self) -> object:
        if self._ocr_engine is None:
            self._ocr_engine = self._create_ocr_engine()
        return self._ocr_engine

    @staticmethod
    def validate_pattern(before_text: str | None, after_text: str | None) -> None:
        """Ensure pattern has at least one boundary token configured."""
        if not (before_text and before_text.strip()) and not (after_text and after_text.strip()):
            raise PatternValidationError("Pattern must define before_text and/or after_text.")

    @staticmethod
    def normalize_for_matching(text: str) -> str:
        """Normalize OCR text for pattern matching: remove newlines, collapse whitespace."""
        text = (text or "").replace("\n", " ").replace("\r", " ")
        return _RE_WHITESPACE.sub(" ", text).strip()

    @staticmethod
    def build_joined_region_text(lines: list[str]) -> str:
        """Build canonical joined text for one frame-region OCR result."""
        kept = [str(line).strip() for line in lines if str(line).strip()]
        return OCRService.normalize_for_matching(" ".join(kept))

    @staticmethod
    def _is_valid_candidate_token(token: str) -> bool:
        return bool(re.search(r"[A-Za-z0-9]", token or ""))

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

        Returns (token, name_start_pos, token_count_between_boundaries),
        or None if no match.
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
            if len(tokens) > 6:
                return None
            token = tokens[0] if tokens else ""  # both-boundary: first token between markers
            if not token:
                return None
            return token, b_range[1], len(tokens)

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
            return token, b_range[1], 1

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
        return token, 0, 1

    def extract_candidates(
        self,
        lines: list[str],
        patterns: list[ContextPattern] | None = None,
        filter_non_matching: bool = False,
        tolerance_threshold: float = 0.75,
    ) -> list[tuple[str, str | None]]:
        """Extract candidate names from OCR lines using optional context patterns.

        Returns tuples of (candidate_name, matched_pattern_id).
        """
        decisions = self.evaluate_lines(
            lines,
            patterns=patterns,
            filter_non_matching=filter_non_matching,
            tolerance_threshold=tolerance_threshold,
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
        tolerance_threshold: float = 0.75,
    ) -> list[dict[str, object]]:
        """Evaluate OCR lines and return accept/reject decisions with reasons.

        Each decision includes: raw_string, tested_string_raw, tested_string_normalized,
        accepted, rejection_reason, extracted_name, matched_pattern.
        """
        active_patterns = [pattern for pattern in (patterns or []) if pattern.enabled]
        source_lines = [str(line).strip() for line in lines if str(line).strip()]
        if not source_lines:
            return []

        source_raw = "\n".join(source_lines)
        tested_normalized = OCRService.build_joined_region_text(source_lines)

        matched_candidates: list[tuple[str, str, int, int, int]] = []
        for pattern_index, pattern in enumerate(active_patterns):
            try:
                meta = self._extract_with_boundaries_meta(
                    tested_normalized,
                    before_text=pattern.before_text,
                    after_text=pattern.after_text,
                    threshold=tolerance_threshold,
                )
            except PatternValidationError:
                continue

            if meta:
                extracted, start_pos, token_count = meta
                matched_candidates.append(
                    (extracted, pattern.id, token_count, start_pos, pattern_index)
                )

        if matched_candidates:
            # Deterministic conflict resolution: nearest span (fewest tokens),
            # then earliest start, then pattern order.
            selected = sorted(matched_candidates, key=lambda item: (item[2], item[3], item[4]))[0]
            extracted_name = selected[0].strip()
            if not OCRService._is_valid_candidate_token(extracted_name):
                return [
                    {
                        "raw_string": source_raw,
                        "tested_string_raw": source_raw,
                        "tested_string_normalized": tested_normalized,
                        "accepted": False,
                        "rejection_reason": "invalid_token",
                        "extracted_name": "",
                        "matched_pattern": selected[1],
                    }
                ]

            return [
                {
                    "raw_string": source_raw,
                    "tested_string_raw": source_raw,
                    "tested_string_normalized": tested_normalized,
                    "accepted": True,
                    "rejection_reason": "",
                    "extracted_name": extracted_name,
                    "matched_pattern": selected[1],
                }
            ]

        if not filter_non_matching:
            return [
                {
                    "raw_string": source_raw,
                    "tested_string_raw": source_raw,
                    "tested_string_normalized": tested_normalized,
                    "accepted": True,
                    "rejection_reason": "",
                    "extracted_name": tested_normalized,
                    "matched_pattern": None,
                }
            ]

        return [
            {
                "raw_string": source_raw,
                "tested_string_raw": source_raw,
                "tested_string_normalized": tested_normalized,
                "accepted": False,
                "rejection_reason": "no_pattern_match",
                "extracted_name": "",
                "matched_pattern": None,
            }
        ]
