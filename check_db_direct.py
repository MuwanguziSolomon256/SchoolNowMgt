import sqlite3

db_path = r'c:\Users\Admin\Desktop\SchoolNowMgt\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Schools ===")
cursor.execute("SELECT id, name FROM school_school")
schools = cursor.fetchall()
for school_id, name in schools:
    print(f"  ID: {school_id}, Name: {name}")

print("\n=== Teachers with Role ===")
cursor.execute("""
    SELECT u.id, u.username, u.email, u.role, u.school_id 
    FROM SchoolNowMgt_customuser u 
    WHERE u.role = 'teacher'
    LIMIT 10
""")
teachers = cursor.fetchall()
for user_id, username, email, role, school_id in teachers:
    print(f"  {username} ({user_id}): role={role}, school_id={school_id}")

print("\n=== Staff Profiles (DOS) ===")
cursor.execute("""
    SELECT sp.id, u.username, sp.teacher_admin_role, sp.school_id
    FROM teacher_staffprofile sp
    JOIN SchoolNowMgt_customuser u ON sp.user_id = u.id
    WHERE sp.teacher_admin_role = 'dos'
""")
dos_profiles = cursor.fetchall()
if dos_profiles:
    for staff_id, username, role, school_id in dos_profiles:
        print(f"  {username} ({staff_id}): role={role}, school_id={school_id}")
else:
    print("  No DOS users found")

conn.close()
