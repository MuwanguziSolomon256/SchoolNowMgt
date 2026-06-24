#!/usr/bin/env python
"""Check test users and their school assignments"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

print("\n" + "="*70)
print("  TEST USERS AND SCHOOL ASSIGNMENTS")
print("="*70)

# Get DOS users by school
c.execute("""
SELECT u.email, u.first_name, s.teacher_admin_role, sch.name
FROM SchoolNowMgt_customuser u
JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
JOIN SchoolNowMgt_school sch ON s.school_id = sch.id
WHERE s.teacher_admin_role = 'dos'
ORDER BY s.school_id
""")

print("\nDOS (Director of Studies) Users:")
dos_users = c.fetchall()
for email, first_name, role, school in dos_users:
    print(f"  - {email} ({first_name}) -> {school}")

# Get Deputy HM users
c.execute("""
SELECT u.email, u.first_name, s.teacher_admin_role, sch.name
FROM SchoolNowMgt_customuser u
JOIN SchoolNowMgt_staffprofile s ON u.id = s.user_id
JOIN SchoolNowMgt_school sch ON s.school_id = sch.id
WHERE s.teacher_admin_role = 'deputy_hm'
ORDER BY s.school_id
""")

print("\nDeputy HM Users:")
deputy_users = c.fetchall()
for email, first_name, role, school in deputy_users:
    print(f"  - {email} ({first_name}) -> {school}")

# Get class data by school
c.execute("""
SELECT sch.id, sch.name, COUNT(cg.id) as class_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_classgrade cg ON sch.id = cg.school_id
GROUP BY sch.id, sch.name
""")

print("\nClasses by School:")
for sch_id, sch_name, class_count in c.fetchall():
    print(f"  School {sch_id} ({sch_name}): {class_count} classes")

# Get student data by school
c.execute("""
SELECT sch.id, sch.name, COUNT(st.id) as student_count
FROM SchoolNowMgt_school sch
LEFT JOIN SchoolNowMgt_classgrade cg ON sch.id = cg.school_id
LEFT JOIN SchoolNowMgt_student st ON cg.id = st.class_grade_id
GROUP BY sch.id, sch.name
""")

print("\nStudents by School:")
for sch_id, sch_name, student_count in c.fetchall():
    print(f"  School {sch_id} ({sch_name}): {student_count} students")

conn.close()
print("\n" + "="*70)
