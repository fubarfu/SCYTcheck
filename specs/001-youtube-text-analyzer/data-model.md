# Data Model: YouTube Text Analyzer

**Date**: April 11, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Entities

### VideoAnalysis
Represents a single video analysis session.

**Attributes**:
- `url` (string): YouTube video URL
- `timestamp` (datetime): When analysis was performed
- `text_strings` (list[TextString]): Detected text strings

**Relationships**:
- Contains multiple TextString instances

### TextString
Represents a detected text string from user-defined regions.

**Attributes**:
- `content` (string): The detected text
- `x` (int): X-coordinate of region top-left
- `y` (int): Y-coordinate of region top-left
- `width` (int): Width of region
- `height` (int): Height of region
- `frequency` (int): How many times this text appeared in the region

**Relationships**:
- Belongs to VideoAnalysis

## Data Flow

1. User inputs URL → VideoAnalysis created
2. Video frames processed → TextString instances added
3. Analysis complete → CSV exported from TextString list