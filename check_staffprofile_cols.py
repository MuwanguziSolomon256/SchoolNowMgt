import sqlite3

db_path = r'c:\Users\Admin\Desktop\SchoolNowMgt\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Staff Profile Columns ===")
cursor.execute("PRAGMA table_info(SchoolNowMgt_staffprofile)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col}")

print("\n=== Staff Profiles ===")
cursor.execute("""
    SELECT sp.id, sp.user_id, cu.username, sp.teacher_admin_role
    FROM SchoolNowMgt_staffprofile sp
    LEFT JOIN SchoolNowMgt_customuser cu ON sp.user_id = cu.id
    LIMIT 15
""")
staff_profiles = cursor.fetchall()
for sp_id, user_id, username, admin_role in staff_profiles:
    print(f"  {sp_id}: user={username} ({user_id}), role={admin_role}")

conn.close()
