import sqlite3
c = sqlite3.connect('db.sqlite3').cursor()
c.execute('SELECT email, password FROM SchoolNowMgt_customuser WHERE email IN ("dos@test.com", "dos2@test.com")')
for email, pwd in c.fetchall():
    print(f'{email}:\n  {pwd}\n')
