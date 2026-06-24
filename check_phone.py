import sqlite3
c = sqlite3.connect('db.sqlite3').cursor()
c.execute("SELECT email, phone FROM SchoolNowMgt_customuser LIMIT 3")
for row in c.fetchall():
    print(row)
