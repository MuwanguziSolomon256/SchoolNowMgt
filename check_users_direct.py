import sqlite3

db_path = r'c:\Users\Admin\Desktop\SchoolNowMgt\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Schools ===")
cursor.execute("SELECT id, name FROM SchoolNowMgt_school")
schools = cursor.fetchall()
for school_id, name in schools:
    print(f"  ID: {school_id}, Name: {name}")

print("\n=== All Teachers ===")
cursor.execute("""
    SELECT id, username, email, role, school_id 
    FROM SchoolNowMgt_customuser
    WHERE role = 'teacher'
    LIMIT 15
""")
teachers = cursor.fetchall()
for user_id, username, email, role, school_id in teachers:
    print(f"  {user_id}: {username} ({email}), school_id={school_id}")

print("\n=== Staff Profiles ===")
cursor.execute("""
    SELECT sp.id, sp.user_id, cu.username, sp.teacher_admin_role, sp.school_id
    FROM SchoolNowMgt_staffprofile sp
    LEFT JOIN SchoolNowMgt_customuser cu ON sp.user_id = cu.id
    LIMIT 15
""")
staff_profiles = cursor.fetchall()
for sp_id, user_id, username, admin_role, school_id in staff_profiles:
    print(f"  {sp_id}: user={username} ({user_id}), role={admin_role}, school_id={school_id}")

conn.close()
