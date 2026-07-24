import sqlite3
import sys
import os
from django.contrib.auth.hashers import make_password

db_path = r'c:\Users\Admin\Desktop\SchoolNowMgt\db.sqlite3'

# First, let's check what the current do_test user looks like
print("Checking dos_test user...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, username, email FROM SchoolNowMgt_customuser WHERE username='dos_test'")
result = cursor.fetchone()
if result:
    user_id, username, email = result
    print(f"Found: ID={user_id}, username={username}, email={email}")
    print(f"User ID to use: {user_id}")
else:
    print("dos_test user not found!")

conn.close()

# Now use Django to set the password
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SchoolNowMgt.settings')
sys.path.insert(0, r'c:\Users\Admin\Desktop\SchoolNowMgt')

import django
try:
    django.setup()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.get(username='dos_test')
    user.set_password('DosPass123')
    user.save()
    print(f"\nPassword set for dos_test to: DosPass123")
    print(f"Login URL: http://127.0.0.1:8000/auth/")
except Exception as e:
    print(f"Error: {e}")
