# Quickstart: Collapsable Review Groups Development

**Feature**: 010-collapse-player-groups | **Version**: 1.0 | **Date**: 2026-04-25

## Overview

This guide walks through setting up a local development environment, running tests, and validating the collapsible review groups feature end-to-end.

**Prerequisites**:
- Windows 10/11 desktop
- Python 3.11 installed
- Node.js 18+ installed (for React frontend)
- Git clone of SCYTcheck repository on feature branch `010-collapse-player-groups`

---

## Part 1: Backend Setup

### Step 1.1: Activate Python Environment

```powershell
cd c:\Users\SteSt\source\SCYTcheck
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 1.2: Install Dependencies

```powershell
pip install -r requirements.txt
pip install pytest pytest-cov  # Testing
```

**Expected Output**:
```
Successfully installed opencv-python numpy paddleocr paddlepaddle thefuzz yt-dlp...
```

### Step 1.3: Verify Backend Structure

```powershell
# Check existing API structure (from 007-web-player-ui)
ls -Path src/web/api/

# Expected: existing routes and services
```

---

## Part 2: Frontend Setup

### Step 2.1: Install React Dependencies

```powershell
cd src/web/frontend
npm install
```

### Step 2.2: Start Vite Development Server

```powershell
npm run dev
```

**Expected Output**:
```
VITE v5.0.0  ready in 123 ms

➜  Local:   http://localhost:5173/
➜  press h + enter to show help
```

---

## Part 3: Backend API Server

### Step 3.1: Start Flask/FastAPI Server

```powershell
cd src/web/api
python -m uvicorn main:app --reload --host localhost --port 5000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://localhost:5000
INFO:     Application startup complete
```

---

## Part 4: Running Tests

### Step 4.1: Unit Tests (Review Groups Service)

```powershell
cd c:\Users\SteSt\source\SCYTcheck
pytest tests/unit/test_review_groups_service.py -v
```

**Expected Output**:
```
test_validate_candidate_uniqueness_valid ... PASSED
test_validate_candidate_uniqueness_duplicate ... PASSED
test_consensus_detection_all_same ... PASSED
test_consensus_detection_conflicts ... PASSED
```

### Step 4.2: Contract Tests (API Endpoints)

```powershell
pytest tests/contract/test_review_groups_api_010.py -v
```

**Expected Output**:
```
test_get_session_endpoint ... PASSED
test_select_candidate_valid ... PASSED
test_select_candidate_duplicate_error ... PASSED
test_toggle_collapse_with_consensus ... PASSED
```

### Step 4.3: Integration Tests (Full Workflow)

```powershell
pytest tests/integration/test_review_groups_integration.py -v
```

**Expected Output**:
```
test_workflow_load_session_select_candidates_export ... PASSED
test_workflow_conflict_detection_across_groups ... PASSED
```

---

## Part 5: Manual Validation (End-to-End)

### Step 5.1: Prepare Test Video

1. Create a test video file with player names in frames (or use existing fixture)
2. Place at `artifacts/test-runs/test_video.mp4`

### Step 5.2: Run Analysis

```powershell
# Via command line
python -m src.main --video artifacts/test-runs/test_video.mp4 --mode analysis

# Or via GUI (if implemented):
.\run_app.bat
```

**Expected Output**:
```
Starting video analysis...
Extracting frames... [████████████] 100%
Running OCR... [████████████] 100%
Analysis complete. Results saved to: artifacts/test-runs/analysis_result.csv
```

### Step 5.3: Open Review Interface

1. Open browser to `http://localhost:5173/`
2. Navigate to Review tab
3. Select the analysis result file

**Expected UI State**:
- Multiple collapsible groups visible
- Each group shows candidate spellings
- Consensu groups appear collapsed (gray background, chevron-down)
- Conflict groups appear expanded (blue accent, chevron-up)

### Step 5.4: Test Consensus Workflow

1. **Expand a consensus group**: Click chevron-down → group expands
2. **Verify collapse on selection**: 
   - In an expanded conflict group, select a candidate (radio button)
   - Watch group automatically collapse (all candidates now identical)
   - Verify `is_collapsed=true` in DevTools console
3. **Verify validation error**:
   - In a different group, try selecting a candidate that duplicates another group
   - Error message appears inline (red background, ⚠ icon)
   - Error references conflicting group
   - Selection NOT persisted (state unchanged)
4. **Verify rejection workflow**:
   - In a conflict group, right-click (or press 'R') on a candidate
   - Candidate text becomes strikethrough + faded
   - Consensus detection now uses only non-rejected candidates

### Step 5.5: Verify Persistence

1. **Session Persistence**:
   - Make selections and close browser
   - Reopen browser at `http://localhost:5173/`
   - Navigate back to Review tab
   - Verify selections are preserved (consensus spellings intact)

2. **Sidecar JSON**:
   - Navigate to `artifacts/test-runs/`
   - Verify `analysis_result.review.json` exists
   - Open file and verify structure matches data-model.md
   - Check `consensus_spelling` and `is_collapsed` fields

### Step 5.6: Verify CSV Export Unmodified

```powershell
# Original CSV should be unchanged
type artifacts/test-runs/analysis_result.csv | head -5

# Should show original OCR output (not consensus names)
```

---

## Part 6: Development Checklist

### Before Committing

- [ ] All unit tests pass: `pytest tests/unit/`
- [ ] All contract tests pass: `pytest tests/contract/`
- [ ] All integration tests pass: `pytest tests/integration/`
- [ ] Frontend builds without errors: `npm run build` (in frontend dir)
- [ ] Linting passes: `ruff check .` (project root)
- [ ] No console errors in browser DevTools
- [ ] Persistence verified (state survives reload)
- [ ] CSV export verified (original data unchanged)

### Style Guide

**Python**:
```python
# Follow existing project style
# Type hints for all functions
# Docstrings for service methods
# Use logging module for debug/info messages

from src.services.review_groups_service import ReviewGroupsService

def select_candidate(session_id: str, group_id: str, candidate_id: str) -> dict:
    """Select candidate and validate uniqueness.
    
    Args:
        session_id: Review session ID
        group_id: Candidate group ID
        candidate_id: Candidate to select
        
    Returns:
        Dictionary with success status and validation result
    """
    service = ReviewGroupsService()
    return service.select_candidate(session_id, group_id, candidate_id)
```

**TypeScript/React**:
```typescript
// Follow existing 007-web-player-ui component patterns
// Use functional components with hooks
// Props interface for type safety
// Test coverage for interactive components

interface CollapsibleGroupProps {
  group: CandidateGroup;
  onSelect: (candidateId: string) => Promise<void>;
  onToggleCollapse: (collapsed: boolean) => Promise<void>;
}

export const CollapsibleGroup: React.FC<CollapsibleGroupProps> = ({
  group,
  onSelect,
  onToggleCollapse,
}) => {
  // Implementation
};
```

---

## Part 7: Troubleshooting

### Issue: "Session not found" error when loading Review

**Cause**: Sidecar JSON not created yet  
**Solution**:
```powershell
# Delete cache and reload
rm artifacts/test-runs/*.review.json
# Refresh browser at http://localhost:5173/
```

### Issue: Validation error not showing inline

**Cause**: Backend validation service not returning error properly  
**Solution**:
```powershell
# Check backend logs
# Verify POST /api/v1/review-groups/validate is being called
# Add console.log() in React component to debug
```

### Issue: Group not collapsing after consensus

**Cause**: `is_consensus_reached` check not triggered or `is_collapsed` not updated  
**Solution**:
```powershell
# Verify data-model.py has consensus detection logic
# Check sidecar JSON: is_collapsed should be true after last selection
# Add debug logging to review_groups_service.py
```

### Issue: Tests fail with "Module not found"

**Cause**: PYTHONPATH not set  
**Solution**:
```powershell
# Add project root to PYTHONPATH
$env:PYTHONPATH = "c:\Users\SteSt\source\SCYTcheck"
pytest tests/unit/ -v
```

---

## Part 8: Key Files Reference

| File | Purpose |
| --- | --- |
| `src/web/frontend/src/components/CollapsibleGroup.tsx` | Main collapsible group component |
| `src/web/frontend/src/components/CandidateRadioButton.tsx` | Radio button for candidate selection |
| `src/web/frontend/src/components/ValidationFeedback.tsx` | Inline error/success message display |
| `src/web/api/review_groups_service.py` | Backend consensus & validation logic |
| `src/services/review_session_persistence.py` | Sidecar JSON persistence (enhanced) |
| `tests/unit/test_review_groups_service.py` | Unit tests for business logic |
| `tests/contract/test_review_groups_api_010.py` | API contract tests |
| `tests/integration/test_review_groups_integration.py` | End-to-end workflow tests |

---

## Part 9: Performance Validation

### Target Metrics

- **Collapse/expand toggle**: ≤100ms (measured in browser DevTools)
- **Validation feedback**: ≤500ms (API call + UI update)
- **Render 50 groups with 50 candidates each**: <1s (React profiler)
- **Sidecar JSON save**: ≤200ms (file I/O)

### Measurement

```javascript
// In browser console:
performance.mark('group-collapse-start');
// ... click collapse button
performance.mark('group-collapse-end');
performance.measure('collapse', 'group-collapse-start', 'group-collapse-end');
console.log(performance.getEntriesByName('collapse')[0].duration); // Should be < 100ms
```

---

## Part 10: Next Steps

1. **Complete backend service**: Implement `review_groups_service.py` with all methods from contracts
2. **Complete React components**: Implement `CollapsibleGroup.tsx`, `CandidateRadioButton.tsx`, `ValidationFeedback.tsx`
3. **Run integration tests**: Verify full workflow end-to-end
4. **Performance testing**: Measure against targets above
5. **Code review**: Have team review for style/architecture adherence
6. **Merge to main**: Integrate to main branch after sign-off

---

## Quickstart Conclusion

This guide covers all phases of local development for the collapsible review groups feature. Follow the parts in order for smooth setup and validation.

**Questions?** Refer to:
- [Feature Specification](spec.md) for requirements
- [Data Model](data-model.md) for entity definitions
- [API Contract](contracts/review-groups-api.md) for endpoint details
- [Research](research.md) for design rationale
