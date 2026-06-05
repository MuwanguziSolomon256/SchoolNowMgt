import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings.dev')
django.setup()

from SchoolNowMgt.models import CustomUser

# Check admin_test user
admin = CustomUser.objects.filter(username='admin_test').first()
if admin:
    print(f"✓ Admin user found: {admin.username}")
    print(f"  Email: {admin.email}")
    print(f"  Role: {admin.role}")
    print(f"  is_staff: {admin.is_staff}")
    print(f"  is_superuser: {admin.is_superuser}")
    print(f"  School: {admin.school.name}")
    print(f"  is_active: {admin.is_active}")
    
    # Check if is_staff is False - we may need to update it
    if not admin.is_staff:
        print("\n⚠ NOTE: is_staff is False. Admin can access /school/ dashboard but NOT Django /admin/")
else:
    print("✗ Admin user not found!")
