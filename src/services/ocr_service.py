from __future__ import annotations

import cv2
import numpy as np
import pytesseract


class OCRError(RuntimeError):
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
