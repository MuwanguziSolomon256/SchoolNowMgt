#!/usr/bin/env python
"""Phase 5 PROPER SETUP: Create isolated test data for School 2"""
import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

print("\n" + "="*70)
print("  PHASE 5 DATA SETUP: Creating isolated data for School 2")
print("="*70)

# Step 1: Create TeacherDepartment for School 2
print("\nStep 1: Create departments for School 2...")
try:
    c.execute("""
    INSERT INTO SchoolNowMgt_teacherdepartment 
    (school_id, name, department_type, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (2, 'Mathematics', 'mathematics', 'Math Department for School 2', 1))
    print("  ✓ Mathematics department created")
    
    c.execute("""
    INSERT INTO SchoolNowMgt_teacherdepartment 
    (school_id, name, department_type, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, (2, 'Science', 'science', 'Science Department for School 2', 1))
    print("  ✓ Science department created")
    
except Exception as e:
    print(f"  ⚠ Departments might exist: {e}")

# Step 2: Create ClassGrades for School 2
print("\nStep 2: Create classes for School 2...")
class_ids = []
try:
    c.execute("""
    INSERT INTO SchoolNowMgt_classgrade 
    (school_id, name, level, curriculum, capacity)
    VALUES (?, ?, ?, ?, ?)
    """, (2, 'Form 1 - School 2', 1, 'national', 40))
    class_ids.append(c.lastrowid)
    print(f"  ✓ Form 1 created (ID: {c.lastrowid})")
    
    c.execute("""
    INSERT INTO SchoolNowMgt_classgrade 
    (school_id, name, level, curriculum, capacity)
    VALUES (?, ?, ?, ?, ?)
    """, (2, 'Form 2 - School 2', 2, 'national', 35))
    class_ids.append(c.lastrowid)
    print(f"  ✓ Form 2 created (ID: {c.lastrowid})")
    
except Exception as e:
    print(f"  ⚠ Classes might exist: {e}")
    # Get existing classes for School 2
    c.execute("SELECT id FROM SchoolNowMgt_classgrade WHERE school_id = 2")
    class_ids = [row[0] for row in c.fetchall()]

# Step 3: Create Students for School 2
print("\nStep 3: Create students for School 2...")
if class_ids:
    today = date.today().isoformat()
    for i in range(1, 6):
        try:
            c.execute("""
            INSERT INTO SchoolNowMgt_student 
            (admission_number, first_name, last_name, date_of_birth, gender, 
             class_grade_id, parent_name, parent_phone, curriculum, status, date_admitted, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (f'S2STU{i:03d}', f'Student{i}', 'School2', date(2010, i, 1).isoformat(), 
                  'M' if i % 2 == 0 else 'F', class_ids[i % len(class_ids)], 
                  f'Parent Student {i}', '+254700000000', 'national', 'active', today, ''))
            print(f"  ✓ Student {i} created ({f'S2STU{i:03d}'})")
        except Exception as e:
            print(f"  ⚠ Student {i}: {e}")
else:
    print("  ✗ No classes to assign students to")

conn.commit()

# Step 4: Verify the data was created
print("\nStep 4: Verify data in School 2...")
c.execute("SELECT COUNT(*) FROM SchoolNowMgt_classgrade WHERE school_id = 2")
class_count = c.fetchone()[0]
print(f"  Classes in School 2: {class_count}")

c.execute("""
SELECT COUNT(*) FROM SchoolNowMgt_student st
JOIN SchoolNowMgt_classgrade cg ON st.class_grade_id = cg.id
WHERE cg.school_id = 2
""")
student_count = c.fetchone()[0]
print(f"  Students in School 2: {student_count}")

c.execute("SELECT COUNT(*) FROM SchoolNowMgt_teacherdepartment WHERE school_id = 2")
dept_count = c.fetchone()[0]
print(f"  Departments in School 2: {dept_count}")

conn.close()

print("\n" + "="*70)
print("  PHASE 5 DATA SETUP COMPLETE")
print("="*70)
print(f"\nData created for School 2:")
print(f"  - {class_count} classes")
print(f"  - {student_count} students")
print(f"  - {dept_count} departments")
print(f"\nNext: Log in as user from different schools to verify isolation")
