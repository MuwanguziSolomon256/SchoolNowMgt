#!/usr/bin/env python
"""Check class and student distribution across schools"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

print("\n" + "="*70)
print("  PHASE 5 RE-CHECK: DATA DISTRIBUTION BY SCHOOL")
print("="*70)

# Classes by school
c.execute("""
SELECT sch.id, sch.name, COUNT(cg.id) as class_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_classgrade cg ON sch.id = cg.school_id
GROUP BY sch.id, sch.name
ORDER BY sch.id
""")

print("\nClasses by School:")
schools_data = {}
for sch_id, sch_name, class_count in c.fetchall():
    print(f"  School {sch_id} ({sch_name}): {class_count} classes")
    schools_data[sch_id] = {'name': sch_name, 'classes': class_count}

# Students by school
c.execute("""
SELECT sch.id, COUNT(st.id) as student_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_classgrade cg ON sch.id = cg.school_id
LEFT JOIN SchoolNowMgt_student st ON cg.id = st.class_grade_id
GROUP BY sch.id
ORDER BY sch.id
""")

print("\nStudents by School:")
for sch_id, student_count in c.fetchall():
    sch_name = schools_data.get(sch_id, {}).get('name', '?')
    print(f"  School {sch_id} ({sch_name}): {student_count} students")

# Users by school (admin roles)
c.execute("""
SELECT sch.id, sch.name, COUNT(u.id) as user_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_staffprofile sp ON sch.id = sp.school_id
LEFT JOIN SchoolNowMgt_customuser u ON sp.user_id = u.id
WHERE sp.teacher_admin_role != '' OR sp.support_staff_role != ''
GROUP BY sch.id, sch.name
ORDER BY sch.id
""")

print("\nAdministrative Users by School:")
for sch_id, sch_name, user_count in c.fetchall():
    print(f"  School {sch_id} ({sch_name}): {user_count} admin users")

# Department distribution
c.execute("""
SELECT sch.id, sch.name, COUNT(td.id) as dept_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_teacherdepartment td ON sch.id = td.school_id
GROUP BY sch.id, sch.name
ORDER BY sch.id
""")

print("\nDepartments by School:")
for sch_id, sch_name, dept_count in c.fetchall():
    print(f"  School {sch_id} ({sch_name}): {dept_count} departments")

# Specific DOS users and their schools
c.execute("""
SELECT u.email, u.first_name, sp.teacher_admin_role, sch.name
FROM SchoolNowMgt_customuser u
JOIN SchoolNowMgt_staffprofile sp ON u.id = sp.user_id
JOIN SchoolNowMgt_school sch ON sp.school_id = sch.id
WHERE sp.teacher_admin_role = 'dos'
ORDER BY sp.school_id, u.email
""")

print("\nDOS Users by School:")
dos_users = c.fetchall()
for email, first_name, role, school_name in dos_users:
    print(f"  {email} → {school_name}")

if not dos_users:
    print("  ❌ NO DOS USERS FOUND!")

conn.close()

print("\n" + "="*70)
print("ANALYSIS:")
print("="*70)

# Determine isolation status
for sch_id, sch_info in schools_data.items():
    classes = sch_info['classes']
    if classes > 0:
        print(f"\n✅ School {sch_id} ({sch_info['name']}): Has data ({classes} classes)")
    else:
        print(f"\n⚠️  School {sch_id} ({sch_info['name']}): NO DATA (0 classes)")

print("\nConclusion:")
if len([s for s in schools_data.values() if s['classes'] > 0]) >= 2:
    print("✅ PHASE 5 VERIFICATION: Multi-school isolation CAN BE TESTED")
else:
    print("❌ PHASE 5 VERIFICATION: Insufficient data - School 2 appears empty")
    print("   ACTION: Need to create test data for School 2")

