import sqlite3

conn = sqlite3.connect('db.sqlite3')
c = conn.cursor()

# Get password from dos@test.com
c.execute("SELECT password FROM SchoolNowMgt_customuser WHERE email = 'dos@test.com' LIMIT 1")
pwd = c.fetchone()[0]

# Update dos2@test.com with the same password
c.execute("UPDATE SchoolNowMgt_customuser SET password = ? WHERE email = 'dos2@test.com'", (pwd,))
conn.commit()

print('✓ Password updated for dos2@test.com')
print(f'  Password hash: {pwd[:50]}...')

conn.close()
