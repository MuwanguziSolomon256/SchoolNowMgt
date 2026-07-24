from django.contrib.auth.hashers import make_password

# Generate a hash for the password "DosPass123"
password = "DosPass123"
hashed = make_password(password)
print(f"Password: {password}")
print(f"Hashed: {hashed}")
