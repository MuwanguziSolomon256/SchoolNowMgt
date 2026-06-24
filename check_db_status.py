#!/usr/bin/env python
"""Phase 5: Multi-School Isolation - Database Setup via SQL"""
import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

print("\n" + "="*70)
print("  PHASE 5: DATABASE STATUS CHECK")
print("="*70)

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in c.fetchall()]

print("\nUser/Staff Related Tables:")
for table in tables:
    if 'customuser' in table.lower() or 'staffprofile' in table.lower():
        print(f"  - {table}")

print("\nSchool Tables:")
for table in tables:
    if 'school' in table.lower():
        print(f"  - {table}")

# Check schools
c.execute("SELECT id, name FROM SchoolNowMgt_school")
schools = c.fetchall()
print(f"\nSchools in database: {len(schools)}")
for sid, sname in schools:
    print(f"  {sid}: {sname}")

# Look for user table
user_table = None
for table in tables:
    if 'customuser' in table.lower():
        user_table = table
        break

if user_table:
    c.execute(f"SELECT COUNT(*) FROM {user_table}")
    user_count = c.fetchone()[0]
    print(f"\nUsers in {user_table}: {user_count}")
    
    c.execute(f"SELECT COUNT(*) FROM {user_table} WHERE email LIKE '%test%'")
    test_user_count = c.fetchone()[0]
    print(f"Test users: {test_user_count}")

# Check StaffProfile
c.execute("SELECT COUNT(*) FROM SchoolNowMgt_staffprofile")
staff_count = c.fetchone()[0]
print(f"\nStaffProfile records: {staff_count}")

# Check ClassGrade
c.execute("SELECT COUNT(*) FROM SchoolNowMgt_classgrade")
class_count = c.fetchone()[0]
print(f"ClassGrade records: {class_count}")

# Check Students
c.execute("SELECT COUNT(*) FROM SchoolNowMgt_student")
student_count = c.fetchone()[0]
print(f"Student records: {student_count}")

conn.close()
print("\n" + "="*70)
print("Status check complete. Use Django admin to create School 2 data.")
print("="*70)
