# Contract: OCR Service

**Purpose**: Interface for detecting text in image regions.

**Methods**:
- `detect_text(image: np.ndarray, region: tuple) -> list[str]`: Detects text in specified region (x, y, w, h)
- `preprocess_image(image: np.ndarray) -> np.ndarray`: Applies preprocessing for better OCR

**Exceptions**:
- `OCRError`: When text detection fails

**Dependencies**: pytesseract, opencv-python