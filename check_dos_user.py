import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SchoolNowMgt.settings')
django.setup()

from django.contrib.auth import get_user_model
from teacher.models import TeacherProfile, StaffProfile
from school.models import School

User = get_user_model()

print("=== ALL USERS ===")
for user in User.objects.all():
    print(f"  {user.username} (role={user.role}, email={user.email})")

print("\n=== CHECKING TEACHERS WITH DOS ROLE ===")
teachers = User.objects.filter(role='teacher')
for teacher in teachers:
    print(f"\n  {teacher.username}:")
    print(f"    - Role: {teacher.role}")
    try:
        tp = TeacherProfile.objects.get(user=teacher)
        print(f"    - Teacher Profile: {tp.id}")
    except:
        print(f"    - Teacher Profile: NOT FOUND")
    
    try:
        sp = StaffProfile.objects.get(user=teacher)
        print(f"    - Staff Profile Admin Role: {sp.teacher_admin_role}")
        print(f"    - School: {sp.school}")
    except:
        print(f"    - Staff Profile: NOT FOUND")

print("\n=== SCHOOLS ===")
for school in School.objects.all():
    print(f"  {school.name} ({school.id})")

print("\n=== LOOKING FOR DOS USERS ===")
dos_users = StaffProfile.objects.filter(teacher_admin_role='dos')
print(f"Found {dos_users.count()} DOS users:")
for profile in dos_users:
    print(f"  - {profile.user.username} at {profile.school}")
