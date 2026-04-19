# Changelog

## 2026-04-15

### Added
- Multiline OCR normalization support for context matching across line breaks.
- Global matching tolerance control (`0.60` to `0.95`, default `0.75`) in Advanced Settings.
- Frame-change gating controls in Advanced Settings:
  - `Enable Frame-Change Gating` (default on)
  - `Gating threshold` (`0.0` to `1.0`, default `0.02`)
- `GatingStats` model support and export summary formatting.
- New integration and validation tests for SC-001 through SC-005.

### Changed
- Analysis pipeline now supports tolerance propagation and per-region gating decisions.
- Completion status now includes gating summary counters.
- Quickstart and README updated with tuning guidance and troubleshooting for tolerance/gating.
