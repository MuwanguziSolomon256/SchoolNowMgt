import sqlite3

db_path = r'c:\Users\Admin\Desktop\SchoolNowMgt\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=== Available Tables ===")
for table in tables:
    print(f"  {table[0]}")

# Try to find school-related tables
school_tables = [t[0] for t in tables if 'school' in t[0].lower()]
if school_tables:
    print(f"\n=== School-related tables: {school_tables} ===")
    for table_name in school_tables:
        print(f"\nTable: {table_name}")
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            print(f"  Sample data: {rows}")

conn.close()
