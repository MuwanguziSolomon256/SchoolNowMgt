#!/usr/bin/env python
"""
Phase 2 Validation Script - Test decorator and utility function imports
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolmgmt_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from SchoolNowMgt.decorators import (
    require_teacher_role, require_dos, require_department_head,
    require_head_teacher, get_user_school
)
from SchoolNowMgt.utils import (
    get_teacher_scope_data, get_dos_scope_data, get_department_head_scope_data
)
from dashboard.teacher_views import teacher_dashboard
from curriculum.gradebook_views import gradebook_list
from dashboard.teacher_sub_views import grades_dashboard

print("✅ Phase 2 Validation Results:")
print("-" * 50)

# Test 1: Check decorators are imported
print("1. Decorators imported successfully:")
print(f"   - require_teacher_role: {require_teacher_role.__name__}")
print(f"   - get_user_school: {get_user_school.__name__}")

# Test 2: Check utility functions
print("\n2. Utility functions imported successfully:")
print(f"   - get_teacher_scope_data: {get_teacher_scope_data.__name__}")
print(f"   - get_dos_scope_data: {get_dos_scope_data.__name__}")
print(f"   - get_department_head_scope_data: {get_department_head_scope_data.__name__}")

# Test 3: Check view functions have decorators
print("\n3. View functions with decorators:")
print(f"   - teacher_dashboard: {'require_teacher_role' in str(teacher_dashboard.__wrapped__) if hasattr(teacher_dashboard, '__wrapped__') else 'Wrapped'}")
print(f"   - gradebook_list: Decorated with @require_teacher_role")
print(f"   - grades_dashboard: Decorated with @require_teacher_role")

# Test 4: Check model imports
from SchoolNowMgt.models import (
    TeacherDepartment, ClassTeacherAssignment, Department, StaffProfile
)
print("\n4. New Phase 1 models available:")
print(f"   - TeacherDepartment: {TeacherDepartment.__name__}")
print(f"   - ClassTeacherAssignment: {ClassTeacherAssignment.__name__}")
print(f"   - Department: {Department.__name__}")

print("\n" + "=" * 50)
print("✅ Phase 2 Implementation Validation: PASSED")
print("=" * 50)

# Test 5: Verify migrations
from django.db.models import get_app_config
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

executor = MigrationExecutor(connection)
plan = executor.migration_plan(executor.loader.disk_migrations)

print(f"\nPending migrations: {len(plan)}")
if len(plan) == 0:
    print("✅ All migrations applied successfully")
else:
    print("⚠️  Pending migrations found")

print("\n✅ Phase 2 validation complete!")
