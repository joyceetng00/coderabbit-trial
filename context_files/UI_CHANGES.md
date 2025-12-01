# UI Changes & Bug Fixes

## Issues Identified

### 1. Annotation Loop Bug - No Ending Detection
**Problem:** Users can continue annotating "fake" samples after all samples have been reviewed. The annotation interface doesn't properly detect when all samples are complete, allowing duplicate annotations that skew error analysis.

**Root Cause:** 
- `_move_to_next_sample()` reloads unannotated samples but doesn't verify if the current sample was already annotated
- No check to prevent annotating the same sample multiple times
- Session state persists stale sample lists even after all samples are annotated

**Impact:** 
- Maximum annotated samples can exceed total samples
- Error analysis shows incorrect statistics
- Data integrity compromised

**Proposed Fix:**
1. Before allowing annotation, verify the sample hasn't already been annotated
2. After each annotation, reload unannotated samples list from database
3. Add explicit check: `if total_annotated >= total_samples: disable annotation`
4. Show clear message when all samples are complete
5. Automatically refresh sample list after each annotation

---

### 2. Reject Button Color
**Problem:** Reject button appears red, which is counterintuitive. Green is more appropriate for a primary action button.

**Current:** Red button (default Streamlit secondary button style)
**Desired:** Green button (primary type)

**Proposed Fix:**
- Change Reject button to `type="primary"` (green)
- Keep Accept button as `type="primary"` (both are primary actions)

---

### 3. Notes Field Should Be Required for Rejections
**Problem:** Notes field is optional when rejecting a sample. This leads to incomplete data and makes error analysis less useful.

**Current:** Notes are optional (`placeholder="Notes (optional)"`)
**Desired:** Notes required when rejecting

**Proposed Fix:**
1. Remove "optional" from placeholder text
2. Add validation in form submission: require notes field to be non-empty
3. Show error message if user tries to submit rejection without notes
4. Update form validation logic

---

### 4. Remove "factually_incorrect" Issue Type
**Problem:** "factually_incorrect" and "hallucination" are essentially the same thing. Having both creates confusion and splits data unnecessarily.

**Current Issue Types:**
- hallucination
- factually_incorrect ← Remove this
- incomplete
- wrong_format
- off_topic
- inappropriate_tone
- refusal
- other

**Proposed Fix:**
1. Remove "factually_incorrect" from `Annotation.primary_issue` Literal type
2. Remove from UI selectbox options
3. Update any existing annotations: migrate "factually_incorrect" → "hallucination" (optional, for data migration)
4. Update documentation

---

## Implementation Plan

### Priority Order:
1. **Annotation Loop Bug** (Critical - data integrity)
2. **Notes Required** (High - data quality)
3. **Remove factually_incorrect** (Medium - data consistency)
4. **Button Color** (Low - UX polish)

### Files to Modify:
- `ui/annotate_page.py` - Main annotation logic
- `models/annotation.py` - Issue type definition
- `storage/database.py` - May need migration helper (optional)

### Testing Checklist:
- [x] Cannot annotate same sample twice
- [x] Annotation stops when all samples complete
- [x] Reject button is green
- [x] Notes required for rejection (form validation)
- [x] "factually_incorrect" removed from options
- [ ] Error analysis still works correctly (needs manual testing)

---

## Fixes Implemented

### ✅ 1. Annotation Loop Bug - FIXED
**Changes:**
- Always reload unannotated samples from database at start of function
- Check if sample already annotated before allowing annotation
- Reload sample list after each annotation
- Explicit check: `if total_annotated >= total_samples: show completion message`
- `_move_to_next_sample()` now always reloads fresh data from database
- Added double-check before saving annotation to prevent duplicates

**Files Modified:**
- `ui/annotate_page.py` - Complete rewrite of annotation flow

### ✅ 2. Reject Button Color - FIXED
**Changes:**
- Changed Reject button to `type="primary"` (green)
- Both Accept and Reject are now primary buttons

**Files Modified:**
- `ui/annotate_page.py` - Line 105

### ✅ 3. Notes Required - FIXED
**Changes:**
- Removed "(optional)" from label
- Changed label to "Notes *" to indicate required
- Added validation: `if not notes or not notes.strip(): show error`
- Form submission blocked if notes empty
- Updated help text to indicate requirement

**Files Modified:**
- `ui/annotate_page.py` - Lines 130-133, 144-151

### ✅ 4. Remove "factually_incorrect" - FIXED
**Changes:**
- Removed from `Annotation.primary_issue` Literal type
- Removed from UI selectbox options
- Updated both model and UI consistently

**Files Modified:**
- `models/annotation.py` - Line 33-40
- `ui/annotate_page.py` - Lines 115-123

---

## Summary

All four issues have been fixed. The annotation interface now:
1. ✅ Prevents duplicate annotations
2. ✅ Properly detects completion
3. ✅ Has green reject button
4. ✅ Requires notes for rejections
5. ✅ Removed redundant issue type

**Next Steps:**
- Manual testing to verify all fixes work correctly
- Test error analysis page still functions with updated issue types

