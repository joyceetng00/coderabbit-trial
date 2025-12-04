# LabelBench Project Reference

## Executive Summary

**Overall Assessment:** ✅ **Solid foundation with critical fixes needed**

This is a well-thought-out spec for a lightweight annotation tool. The architecture (Models → Database → UI) and technology choices (Streamlit + SQLite + Pydantic) are appropriate for the scope. However, several critical issues must be addressed before building.

---

## 🚨 Critical Issues to Fix Before Building

### 1. **Deprecated `datetime.utcnow()`** ⚠️ HIGH PRIORITY

**Problem:** `datetime.utcnow()` is deprecated in Python 3.12+

**Fix:**
```python
from datetime import datetime, timezone
imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Locations:**
- `models/sample.py` (line 187)
- `models/annotation.py` (line 262)

### 2. **SQLite Connection Management** ⚠️ MEDIUM PRIORITY

**Issue:** Every database method opens/closes connections independently
- Inefficient for batch operations
- No transaction management
- Risk of connection leaks

**Fix:** Use context managers:
```python
@contextmanager
def _get_connection(self):
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### 3. **Metadata JSON Parsing** ⚠️ MEDIUM PRIORITY

**Issue:** No error handling for malformed JSON metadata

**Fix:**
```python
def _parse_metadata(self, metadata_str: str) -> Dict[str, Any]:
    if not metadata_str or metadata_str.strip() == '':
        return {}
    try:
        return json.loads(metadata_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Invalid metadata JSON: {metadata_str}")
        return {}
```

### 4. **Session State Race Conditions** ⚠️ MEDIUM PRIORITY

**Issue:** Multiple `st.rerun()` calls can cause lost form state and index errors

**Fix:** Add bounds checking and state validation in navigation functions

### 5. **Input Validation** ⚠️ LOW-MEDIUM PRIORITY

**Issue:** CSV/JSON import doesn't validate empty fields or invalid characters

**Fix:** Add validation in import functions for required fields and ID formats

---

## 💡 High-Value Improvements

### 1. **Keyboard Shortcuts** ⚠️ HIGH VALUE
- 'A' to Accept, 'R' to Reject, Arrow keys to navigate
- Dramatically speeds up annotation workflow
- Consider `streamlit-shortcuts` library or JavaScript injection

### 2. **Enhanced Progress Tracking**
- Store last viewed sample_id for resume capability
- Show completion percentage prominently
- Add "Resume annotation" button on home page

### 3. **Better Annotation Flow**
- Add "Needs Review" state (beyond Accept/Reject)
- Allow skipping samples to return later
- Support batch operations for obvious cases

### 4. **Improved Error Analysis Dashboard** ⚠️ HIGH DEMO VALUE
- Add filters by date range and metadata
- Comparison view across models/task types
- Trend analysis over time
- Export with context

### 5. **CSV Import Enhancements**
- Preview first 5 rows before import
- Show validation errors per row
- Allow partial import (skip invalid, import valid)
- Summary: "Imported 47/50 samples. 3 rows had errors..."

---

## 🔧 Technology Stack Assessment

### ✅ **Excellent Choices**
- **Streamlit**: Perfect for rapid prototyping and internal tools
- **SQLite**: Right choice for local-first approach, no setup required
- **Pydantic**: Excellent for data validation and type safety
- **Plotly**: Good for interactive charts
- **uv**: Modern, fast package manager

### ⚠️ **Considerations**
- **Streamlit limitations**: Session state can be fragile, limited customization
- **SQLite scaling**: Consider backups and migration strategy if tool grows
- **Performance**: Cache expensive queries, consider pagination for large datasets

---

## 🚀 Performance & UX Optimizations

### Database Performance
```python
@st.cache_data
def get_annotation_stats(db):
    return db.get_annotation_stats()
```

### Memory Management
- Avoid loading all samples into memory for large datasets
- Consider pagination or lazy loading for 10K+ samples

### UI Responsiveness
- Truncate very long text for display
- Add expandable sections for full content
- Optimize render loops

---

## 📋 Testing & Setup Requirements

### Prerequisites
- **Python 3.10+** (check: `python --version`)
- **uv package manager** (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup Workflow
```bash
cd labelbench
uv sync --extra dev          # Install all dependencies
uv run pytest tests/ -v     # Run unit tests
uv run streamlit run app.py  # Start application
```

### Test Dataset Format
**CSV Requirements:**
- Required columns: `id`, `prompt`, `response`
- Optional columns become metadata
- Start with 20-50 diverse samples
- Mix acceptable and problematic responses

**JSON Format:**
```json
{
  "samples": [
    {
      "id": "sample_1",
      "prompt": "question text",
      "response": "answer text",
      "metadata": {"model": "gpt-4", "task_type": "customer_support"}
    }
  ]
}
```

### Testing Checklist
1. ✅ Import functionality works correctly
2. ✅ Annotation saves to database
3. ✅ Error Analysis dashboard displays
4. ✅ Export functionality works
5. ✅ Navigation (Previous/Next/Jump) works
6. ✅ Bounds checking prevents crashes

---

## 🎯 Implementation Priority

### Phase 1: Critical Fixes 
1. Fix `datetime.utcnow()` deprecation
2. Add connection management with context managers
3. Add metadata parsing error handling
4. Add input validation for imports
5. Add bounds checking in navigation

### Phase 2: UX Improvements (HIGH VALUE)
1. Add keyboard shortcuts
2. Improve error analysis dashboard
3. Enhance progress tracking
4. Add sample search/filter functionality

### Phase 3: Demo Prep
1. Create compelling example dataset
2. Add undo functionality
3. Improve CSV import validation feedback
4. Add onboarding/tutorial flow

---

## 🔍 Architecture Strengths

1. **Clear separation of concerns**: Models → Database → UI layers
2. **Local-first approach**: No infrastructure complexity
3. **Test-driven**: Having tests from start prevents regressions
4. **Good incremental structure**: Logical PR progression
5. **Right tool for job**: Streamlit perfect for internal annotation tool

---

## ❓ Future Considerations

### Multi-user Support
- Add annotator_id tracking (field already exists ✓)
- Conflict resolution for same sample annotations
- Per-annotator statistics

### Export Flexibility
- JSON export option
- Filter exports by metadata
- Export only annotations (not full samples)

### Annotation Management
- Allow updating existing annotations
- Support for annotation revisions
- Batch operations ("Accept all with metadata X")

---

## ✅ Final Verdict

**Recommendation:** ✅ **Proceed with critical fixes**

The core architecture is sound. Main issues are:
- Deprecated API usage (easy fix)
- Missing error handling (easy fix)
- UX polish opportunities (nice to have)
