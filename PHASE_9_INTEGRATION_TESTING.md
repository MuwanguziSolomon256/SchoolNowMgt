# Phase 9: Integration & Testing Plan

## Overview
Phase 9 validates that all 8 completed phases work together correctly, with proper role-based access control, multi-school isolation, and edge case handling.

## Test Architecture

### Test Categories
1. **Role Permission Tests** - Verify decorators enforce access control
2. **Multi-School Isolation Tests** - Verify school field filtering on all queries
3. **Dashboard View Tests** - Verify all views render correctly with data
4. **URL Routing Tests** - Verify all 50+ routes resolve correctly
5. **Edge Case Tests** - Verify graceful handling when no class/department/hostel assigned
6. **Template Rendering Tests** - Verify template context variables all present
7. **Pagination Tests** - Verify pagination works across all list views
8. **Filter/Search Tests** - Verify filters and search return correct results

---

## 1. Role Permission Tests

### Test Scope
Validate that @require_teacher_role, @require_support_staff_role, @require_dos, @require_department_head, @require_class_teacher, and @require_shift_supervisor decorators work correctly.

### Test Cases

#### 1.1 Unauthenticated Access
```
Test: Anonymous user tries to access any protected route
Expected: Redirect to login page (302)
Routes to test: All teacher/* routes
```

#### 1.2 Wrong Role Access
```
Test: Parent user tries to access DOS dashboard (/admin/dos/)
Expected: PermissionDenied (403)
Test: Teacher user tries to access admin routes (/admin/dos/)
Expected: PermissionDenied (403)
Test: Non-teaching staff tries to access teacher class dashboard (/class/)
Expected: PermissionDenied (403)
```

#### 1.3 Correct Role Access
```
Test: DOS user can access /admin/dos/ routes
Expected: 200 OK
Test: Class teacher can access /class/ routes
Expected: 200 OK
Test: Matron (welfare_coordinator) can access /matron/ routes
Expected: 200 OK
Test: Department head can access /department/ routes
Expected: 200 OK
```

#### 1.4 Sub-role Restrictions
```
Test: Department head tries to access DOS routes
Expected: PermissionDenied (403)
Test: Deputy HM tries to access class teacher routes
Expected: PermissionDenied (403)
Test: Support staff supervisor tries to access matron routes
Expected: PermissionDenied (403)
```

---

## 2. Multi-School Isolation Tests

### Test Scope
Verify that all queries filter by school and never leak data across schools.

### Test Setup
- Create 2 schools: School A, School B
- Create users in each school with different roles
- Create data (classes, subjects, students, grades) in each school

### Test Cases

#### 2.1 Query Isolation
```
Test: DOS user from School A queries /admin/dos/classes/
Expected: Only School A classes returned
Verify: School B classes NOT in results
Test: Class teacher from School A queries students
Expected: Only School A students returned
Verify: School B students NOT in results
```

#### 2.2 View Isolation
```
Test: Subject dept head from School A views /department/subjects/
Expected: Only School A subjects returned
Test: Matron from School B views /matron/hostels/
Expected: Only School B hostels returned
```

#### 2.3 Cross-School Permission Denial
```
Test: DOS from School A tries to manually access School B data via direct ID access
Expected: Either filtered out or 404
Test: Class teacher from School A tries /class/students/<school_b_student_id>/
Expected: 404 or filtered result
```

---

## 3. Dashboard View Tests

### Test Scope
Verify all 50+ views render with correct data structure and template context.

### Views to Test

#### Phase 2: Teacher Functions (30+ views)
- teacher_dashboard: Context keys (tasks, announcements, schedule, statistics)
- teacher_students_list: Context (page_obj, student_count, filters)
- grades_dashboard: Context (grade_stats, recent_grades)
- message_inbox: Context (messages, unread_count, page_obj)
- attendance_marking: Context (class, attendance_date, students)

#### Phase 3: DOS Dashboard (11 views)
- dos_dashboard: Context (stats_cards, recent_activities)
- classes_list: Context (page_obj, search_query, filters)
- teacher_detail: Context (subject_list, classes_taught, timetable)
- performance_report: Context (class_performance, avg_scores)

#### Phase 4: Deputy HM Dashboard (8 views)
- deputy_dashboard: Context (stats, activities)
- teachers_list: Context (page_obj, department_filter)
- staff_detail: Context (subjects, classes, attendance_records)

#### Phase 5: Support Staff Dashboards (7 views)
- staff_dashboard: Context (stats, quick_actions)
- duties_list: Context (page_obj, duty_schedule)

#### Phase 6: Matron Dashboards (7 views)
- matron_dashboard: Context (hostel_stats, residents, occupancy)
- hostels_list: Context (page_obj, hostel_cards)
- resident_detail: Context (profile, attendance, stats)

#### Phase 7: Subject Department Dashboards (8 views)
- dept_dashboard: Context (department_stats, subject_grid)
- teachers_list: Context (page_obj, position_filter)
- class_performance: Context (subject_performance, charts)

#### Phase 8: Class Teacher Dashboards (7 views)
- class_dashboard: Context (stats_grid, actions, recent_grades, no_class flag)
- students_list: Context (page_obj, search_query)
- student_detail: Context (grades, attendance, statistics)
- grades_management: Context (page_obj, subject_filter)
- attendance_management: Context (page_obj, date_filter, status_filter)
- class_performance: Context (subject_performance, summary_stats)
- parent_communications: Context (page_obj, message_history)

### Test Structure
For each view:
```python
def test_<view_name>_context():
    # 1. Create user with correct role
    # 2. Create test data in user's school
    # 3. GET /route/
    # 4. Assert status 200
    # 5. Assert all context keys present
    # 6. Assert data is from user's school only
```

---

## 4. URL Routing Tests

### Test Scope
Verify all 7 namespaced route groups resolve correctly.

### Route Groups to Test
1. **teacher/** (50+ routes)
   - Verify all paths resolve to correct views
   - Verify URL names match view functions

2. **teacher/admin/dos/** (11 routes)
   - namespace='dos'
   - All routes accessible under /teacher/admin/dos/

3. **teacher/admin/deputy/** (8 routes)
   - namespace='deputy_hm'
   - All routes accessible under /teacher/admin/deputy/

4. **teacher/support/** (7 routes)
   - namespace='support_staff'
   - All routes accessible under /teacher/support/

5. **teacher/matron/** (7 routes)
   - namespace='matron'
   - All routes accessible under /teacher/matron/

6. **teacher/department/** (8 routes)
   - namespace='subject_dept'
   - All routes accessible under /teacher/department/

7. **teacher/class/** (7 routes)
   - namespace='class_teacher'
   - All routes accessible under /teacher/class/

### Test Structure
```python
def test_url_routing():
    # Test each namespace + path combination
    # Verify reverse() works with namespace:name
    # Verify URL pattern matches view
    # Verify 404 on invalid routes
```

---

## 5. Edge Case Tests

### Test Scope
Verify graceful handling of users with incomplete assignments.

### Edge Cases

#### 5.1 No Class Assigned
```
Test: Class teacher with no class assigned accesses /class/
Expected: View renders with no_class=True flag
Expected: Alert displayed: "You have not been assigned as a class teacher yet"
Expected: No error, no 500
```

#### 5.2 No Department Assigned
```
Test: Subject department head with no department assigned
Expected: View renders with no_department flag
Expected: Graceful message displayed
```

#### 5.3 No Hostel Assigned
```
Test: Matron/welfare coordinator with no hostel assigned
Expected: View renders with stats = 0
Expected: Empty hostel list displayed
```

#### 5.4 Empty Data Sets
```
Test: DOS views class with 0 students
Expected: Class displays, student count = 0
Expected: Empty state message shown
Test: Subject dept with 0 subjects assigned
Expected: Empty state message
Test: Class with 0 grades entered
Expected: "No grades found" message
```

#### 5.5 Pagination Edge Cases
```
Test: Page 1 of 1 (only 1 page of results)
Expected: No prev/next links shown
Test: Page number > max_pages requested
Expected: Redirect to last page
Test: Page number < 1 requested
Expected: Redirect to page 1
Test: Invalid page number format
Expected: Redirect to page 1
```

---

## 6. Template Rendering Tests

### Test Scope
Verify all 50+ templates render without context errors.

### Template Test Categories

#### 6.1 Context Variable Presence
For each template:
```python
def test_template_context():
    # Render template with all expected variables
    # Assert no "TemplateSyntaxError" 
    # Assert no "VariableDoesNotExist" errors
    # Assert CSS loads (Tailwind CDN)
```

#### 6.2 Pagination Display
```
Test: Templates with pagination render page links
Expected: "« First", "‹ Previous", "Next ›", "Last »" visible
Test: Single page result hides pagination
Expected: Pagination section not displayed
```

#### 6.3 Filter Controls
```
Test: Search input renders correctly
Expected: Search form submits with GET
Test: Status dropdown renders options
Expected: All status options available
Test: Date picker input renders
Expected: Date format correct
```

#### 6.4 Status Badges
```
Test: Badge colors display for different statuses
Expected: Present = green, Absent = red, Active = green, Inactive = red
Test: Badge classes apply CSS correctly
Expected: Proper background and text color
```

---

## 7. Pagination Tests

### Test Scope
Verify pagination works across all list views (50+ items).

### List Views with Pagination
- DOS: classes_list (15/page), teachers_list (15/page), grades_list (20/page)
- Deputy HM: teachers_list (15/page), staff_list (15/page), notifications_list (10/page)
- Support Staff: duties_list (15/page)
- Matron: hostels_list (15/page), residents_list (20/page)
- Subject Dept: teachers_list (15/page), subjects_list (15/page), classes_list (15/page)
- Class Teacher: students_list (20/page), grades_management (20/page), attendance_management (20/page), parent_communications (15/page)

### Test Cases
```
Test: Navigate through pages with ?page=N
Expected: Correct items displayed for each page
Test: Items per page matches configuration
Expected: Page 1 shows first N items
Test: Last page truncated correctly
Expected: Remaining items on last page
Test: Invalid page number handled
Expected: Redirect to page 1 or last page
```

---

## 8. Filter/Search Tests

### Test Scope
Verify all filter and search functionality returns correct subsets.

### Filter Tests

#### 8.1 Text Search
```
Test: Search "john" in students_list
Expected: Returns students with "john" in name/email
Test: Search case-insensitive
Expected: "JOHN" = "john" = "John"
Test: Empty search returns all
Expected: No results hidden
```

#### 8.2 Status Filter
```
Test: Filter by status="present"
Expected: Only present records returned
Test: Filter by status="absent"
Expected: Only absent records returned
```

#### 8.3 Date Filter
```
Test: Filter by specific date
Expected: Only records for that date returned
Test: Date range filter
Expected: Records within range returned
```

#### 8.4 Dropdown Filter
```
Test: Filter subjects by dropdown
Expected: Only selected subject records returned
Test: "All" option shows all records
Expected: No filtering applied
```

---

## Test Execution Plan

### Step 1: Run Django Tests
```bash
python manage.py test SchoolNowMgt.tests
python manage.py test dashboard.tests
python manage.py test authentication.tests
```

### Step 2: Manual Testing Checklist
- [ ] Test each role's dashboard renders (no 500 errors)
- [ ] Test URL routing for all 7 namespaces
- [ ] Test multi-school isolation (2+ schools)
- [ ] Test edge cases (no class, no department, empty data)
- [ ] Test pagination on all list views
- [ ] Test filters on all filtered views
- [ ] Test permission denial for wrong roles

### Step 3: Browser Testing
- Chrome/Edge: Verify CSS renders
- Mobile: Verify responsive design
- Performance: Check page load times

---

## Expected Test Results

### Passing Criteria
- ✅ 0 role permission bypass vulnerabilities
- ✅ 0 multi-school data leaks
- ✅ 0 unhandled template errors (500 status)
- ✅ 0 invalid URL routing
- ✅ All edge cases gracefully handled
- ✅ All pagination working
- ✅ All filters returning correct data
- ✅ All 50+ views render with 200 status

### Success Metrics
- 100% route coverage
- 0 PermissionDenied bypass
- 0 data isolation failures
- < 200ms average page load

---

## Known Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| School field missing on query | Audit all QuerySets for school= filter |
| Role decorator bypass | Manual permission testing per role |
| Template variable missing | Test template rendering with min context |
| Pagination breaks on 1 page | Handle edge case in paginator |
| Search doesn't sanitize input | Use Django ORM Q() objects (safe) |

---

## Rollback Plan
If critical issues found:
1. Identify affected phase (1-8)
2. Revert changes to that phase
3. Fix issue in isolated branch
4. Re-run Phase 9 tests
5. Proceed to Phase 10

---

## Next Steps After Phase 9
- Document all validation results
- Generate test coverage report
- Proceed to Phase 10 (Documentation & Deployment)
- Deploy to PythonAnywhere with Phase 9 tests passing
