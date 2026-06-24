#!/usr/bin/env python
"""
Phase 6: Edge Case Testing
===========================
Tests system robustness with edge cases (SQLite-based, no Django imports)
"""

import sqlite3

def test_anonymous_access():
    """Test 1: Anonymous users redirected to login"""
    print("\n[Test 1] Anonymous Access Protection")
    print("  Expected: Anonymous access to /teacher/admin/dos/ -> redirect to login")
    print("  Status: Manual test required via browser")
    print("  Result: DEFERRED (needs browser verification)")

def test_missing_department():
    """Test 2: User with role but no department assignment"""
    print("\n[Test 2] Missing Department Relationship")
    
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    
    # Check for DOS users without departments
    c.execute("""
    SELECT u.email, u.first_name, s.teacher_admin_role
    FROM SchoolNowMgt_customuser u
    JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
    WHERE s.teacher_admin_role = 'dos' AND s.teacher_department_id IS NULL
    """)
    
    orphaned = c.fetchall()
    if orphaned:
        print(f"  Found {len(orphaned)} DOS users without department:")
        for email, first_name, role in orphaned:
            print(f"    - {email} ({first_name})")
        print("  Status: IDENTIFIED - These users might have limited functionality")
    else:
        print("  Status: OK - All DOS users have departments assigned")
    
    conn.close()

def test_empty_classes():
    """Test 3: Dashboard with empty classes (no students)"""
    print("\n[Test 3] Empty Classes Scenario")
    
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    
    c.execute("""
    SELECT cg.name, cg.school_id, COUNT(st.id) as student_count
    FROM SchoolNowMgt_classgrade cg
    LEFT JOIN SchoolNowMgt_student st ON cg.id = st.class_grade_id
    GROUP BY cg.id
    HAVING student_count = 0
    """)
    
    empty_classes = c.fetchall()
    print(f"  Found {len(empty_classes)} empty classes")
    for class_name, school_id, count in empty_classes[:3]:
        print(f"    - {class_name} (School {school_id}, {count} students)")
    print("  Status: IDENTIFIED - System should handle zero-student classes gracefully")
    
    conn.close()

def test_permission_boundaries():
    """Test 4: Permission boundary conditions"""
    print("\n[Test 4] Permission Boundaries")
    
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    
    # Count users by role
    c.execute("""
    SELECT s.teacher_admin_role, COUNT(u.id) as user_count
    FROM SchoolNowMgt_customuser u
    JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
    WHERE s.teacher_admin_role != ''
    GROUP BY s.teacher_admin_role
    """)
    
    roles = c.fetchall()
    print("  Administrative roles in system:")
    for role, count in roles:
        if role:
            print(f"    - {role}: {count} users")
    
    # Check for users with multiple roles
    c.execute("""
    SELECT u.email, s.teacher_admin_role, s.support_staff_role
    FROM SchoolNowMgt_customuser u
    JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
    WHERE (s.teacher_admin_role != '' AND s.teacher_admin_role IS NOT NULL)
      AND (s.support_staff_role != '' AND s.support_staff_role IS NOT NULL)
    """)
    
    dual_role = c.fetchall()
    if dual_role:
        print(f"\n  Found {len(dual_role)} users with DUAL roles:")
        for email, admin_role, support_role in dual_role[:3]:
            print(f"    - {email}: {admin_role} + {support_role}")
        print("  Status: WARNING - Dual roles might cause access ambiguity")
    else:
        print("\n  Status: OK - Role separation is clean")
    
    conn.close()

def test_user_account_states():
    """Test 5: User account edge cases"""
    print("\n[Test 5] User Account States")
    
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    
    # Check inactive users
    c.execute("""
    SELECT COUNT(*) FROM SchoolNowMgt_customuser WHERE is_active = 0
    """)
    inactive = c.fetchone()[0]
    print(f"  Inactive users: {inactive}")
    
    # Check deleted staff
    c.execute("""
    SELECT u.email, s.date_left
    FROM SchoolNowMgt_customuser u
    JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
    WHERE s.date_left IS NOT NULL
    LIMIT 5
    """)
    
    deleted = c.fetchall()
    if deleted:
        print(f"  Staff with date_left set: {len(deleted)}")
        for email, date_left in deleted[:3]:
            print(f"    - {email} (left: {date_left})")
        print("  Status: WARNING - Should prevent access for departed staff")
    else:
        print("  Status: OK - No deleted staff records")
    
    conn.close()

def main():
    print("\n" + "="*70)
    print("  PHASE 6: EDGE CASE TESTING")
    print("="*70)
    
    test_anonymous_access()
    test_missing_department()
    test_empty_classes()
    test_permission_boundaries()
    test_user_account_states()
    
    print("\n" + "="*70)
    print("  PHASE 6 SUMMARY")
    print("="*70)
    print("\nEdge Cases Identified:")
    print("  1. Anonymous access - browser verification needed")
    print("  2. Missing department relationships - needs investigation")
    print("  3. Empty classes - dashboard should handle gracefully")
    print("  4. Dual role conflicts - might cause permission ambiguity")
    print("  5. Deleted/inactive users - access control needed")
    print("\nRecommendations:")
    print("  - Add is_active checks to access decorators")
    print("  - Add date_left validation for staff")
    print("  - Implement single-role enforcement")
    print("  - Handle empty class scenarios in templates")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
