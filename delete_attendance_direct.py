#!/usr/bin/env python
"""Delete today's attendance records from SQLite database."""

import sqlite3
from datetime import date

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get today's date as string
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')

# Delete from teacher attendance table specifically
cursor.execute('DELETE FROM SchoolNowMgt_teacherattendance WHERE date=?', (today,))
conn.commit()

deleted_count = cursor.rowcount
conn.close()

print(f"✓ Deleted {deleted_count} attendance record(s) for {today}")
