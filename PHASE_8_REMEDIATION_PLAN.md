# Phase 8: Remediation of Known Issues - Plan & Execution

**Status**: 🔧 IN PROGRESS  
**Date**: June 22, 2026  
**Objective**: Fix pre-existing bugs identified during Phase 7 integration testing  
**Target**: All issues resolved, system fully functional

---

## Known Issues (From Phase 7 Testing)

### Issue #1: Department List View - ValueError ❌

**Severity**: Medium (Can't view list, but can create/edit)  
**Location**: `dashboard/dos_department_views.py` - `departments_list()` function  
**Error**: `ValueError: Cannot query "Mathematics (Test School)": Must be "Subject" instance.`  
**URL**: `/teacher/admin/dos/departments/`  

**Problem**:
```
The query is trying to filter departments with a Subject object when it should be filtering by Subject FK
```

**Impact**: DOS user cannot view the list of departments, but can still:
- Create new departments ✅
- View department details ✅
- Edit departments ✅
- Delete departments ✅

**Expected Fix**: Review the ORM query for department list filtering and correct the Subject relationship handling.

---

### Issue #2: (To Be Discovered)

**Status**: Investigating...

---

## Pre-Phase 8 Investigation

### What We Know About the Department Model

From earlier investigation:
- Department has a `head` FK to Teacher
- Department has `subjects` M2M relationship
- Query was failing on Subject filtering

### Next Steps

1. **Inspect `dos_department_views.py`** - Find departments_list function
2. **Identify ORM query error** - Find the problematic filter
3. **Review Department model** - Confirm relationships
4. **Fix the query** - Correct the Subject filtering
5. **Test the fix** - Verify departments list page loads
6. **Verify no regression** - Ensure other department views still work

---

## Fix Execution Queue

- [ ] Fix Issue #1: Department list ValueError
- [ ] Verify fix doesn't break other functions
- [ ] Search for similar ORM patterns (may have same bug elsewhere)
- [ ] Run regression tests
- [ ] Document fix and resolution

---

## Additional Investigation Areas

1. **Matron secondary views** - Haven't tested due to permission blocks
2. **Support Staff secondary views** - Haven't tested due to permission blocks
3. **Department Head secondary views** - Haven't tested due to permission blocks
4. **Class Teacher secondary views** - Haven't tested due to permission blocks
5. **Parent system** - Not tested in Phase 7
6. **Teacher portal** - Not tested in Phase 7

These should be tested in Phase 7 Part 2 after Issue #1 is fixed.

---

## Success Criteria for Phase 8

- [ ] Department list page loads without errors
- [ ] Department create/edit/delete still working
- [ ] No new errors introduced
- [ ] Similar ORM patterns reviewed and fixed if needed
- [ ] All Phase 7 tests still pass
- [ ] Ready for Phase 9: Security Audit
