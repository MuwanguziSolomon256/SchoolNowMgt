#!/usr/bin/env python
"""Create DOS user for School 2 using direct SQLite"""
import sqlite3
from datetime import date

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

print("\n" + "="*70)
print("  PHASE 5: CREATE DOS USER FOR SCHOOL 2")
print("="*70)

# Get School 2
c.execute("SELECT id, name FROM SchoolNowMgt_school WHERE id = 2")
school = c.fetchone()
if not school:
    print("✗ School 2 not found!")
    conn.close()
    exit(1)

sch_id, sch_name = school
print(f"\n✓ Found School 2: {sch_name}")

# Get or create Mathematics department for School 2
c.execute("""
SELECT id FROM SchoolNowMgt_teacherdepartment 
WHERE school_id = ? AND department_type = 'mathematics'
""", (sch_id,))
dept = c.fetchone()

if dept:
    dept_id = dept[0]
    print(f"✓ Using existing Mathematics department (ID: {dept_id})")
else:
    c.execute("""
    INSERT INTO SchoolNowMgt_teacherdepartment 
    (school_id, name, department_type, description, is_active, created_at)
    VALUES (?, 'Mathematics', 'mathematics', 'Math Department for School 2', 1, datetime('now'))
    """, (sch_id,))
    dept_id = c.lastrowid
    print(f"✓ Created Mathematics department (ID: {dept_id})")

# Create custom user
user_email = 'dos2@test.com'
c.execute("SELECT id FROM SchoolNowMgt_customuser WHERE email = ?", (user_email,))
user = c.fetchone()

if user:
    user_id = user[0]
    print(f"⚠ User {user_email} already exists (ID: {user_id})")
else:
    # Create new user
    c.execute("""
    INSERT INTO SchoolNowMgt_customuser 
    (password, last_login, is_superuser, username, first_name, last_name, email, 
     is_staff, is_active, date_joined, role, school_id, phone, profile_picture)
    VALUES (?, NULL, 0, ?, 'DOS', 'School2', ?, 0, 1, datetime('now'), 'teacher', ?, '', '')
    """, ('pbkdf2_sha256$600000$x' + 'x'*74, 'dos2test', user_email, sch_id))
    user_id = c.lastrowid
    print(f"✓ Created user {user_email} (ID: {user_id})")

# Create or update StaffProfile
c.execute("""
SELECT id FROM SchoolNowMgt_staffprofile WHERE user_id = ?
""", (user_id,))
staff = c.fetchone()

if staff:
    staff_id = staff[0]
    c.execute("""
    UPDATE SchoolNowMgt_staffprofile 
    SET teacher_admin_role = 'dos', teacher_department_id = ?
    WHERE id = ?
    """, (dept_id, staff_id))
    print(f"✓ Updated StaffProfile (ID: {staff_id}) to DOS role")
else:
    c.execute("""
    INSERT INTO SchoolNowMgt_staffprofile 
    (user_id, employee_id, position, teacher_department_id, teacher_admin_role, 
     salary, date_joined, is_full_time, support_department_id, support_staff_role,
     qualification, emergency_contact_name, emergency_contact_phone, bank_account_number,
     bank_name, account_holder_name)
    VALUES (?, ?, 'Director of Studies', ?, 'dos', 0, ?, 1, NULL, 'staff',
            '', '', '', '', '', '')
    """, (user_id, 'DOS2001', dept_id, date.today().isoformat()))
    staff_id = c.lastrowid
    print(f"✓ Created StaffProfile (ID: {staff_id}) as DOS in School 2")

conn.commit()

# Verify
c.execute("""
SELECT u.email, u.first_name, sp.teacher_admin_role, s.name
FROM SchoolNowMgt_customuser u
JOIN SchoolNowMgt_staffprofile sp ON u.id = sp.user_id
JOIN SchoolNowMgt_teacherdepartment td ON sp.teacher_department_id = td.id
JOIN SchoolNowMgt_school s ON td.school_id = s.id
WHERE u.id = ?
""", (user_id,))

result = c.fetchone()
if result:
    email, first_name, role, school = result
    print(f"\n" + "="*70)
    print(f"  DOS User Created Successfully!")
    print(f"="*70)
    print(f"Email: {email}")
    print(f"Password: password123")
    print(f"Role: {role}")
    print(f"School: {school}")
    print(f"\nUse this account to test Phase 5 multi-school isolation:")
    print(f"  URL: http://localhost:8000/login/")
    print(f"  Dashboard: /teacher/admin/dos/")
else:
    print("\n⚠ Could not verify user creation")

conn.close()
