"""
URL configuration for Support Staff Dashboards

Namespace: support_staff (accessed as 'support_staff:...')
Base path: /teacher/support/

Includes routes for:
- Department Head dashboard and staff management
- Shift Supervisor attendance and shift management
- Welfare Coordinator dashboard
"""

from django.urls import path
from dashboard.support_staff_views import (
    # Department Head Views
    dept_head_dashboard,
    dept_head_staff_list,
    dept_head_staff_detail,
    
    # Shift Supervisor Views
    shift_supervisor_dashboard,
    shift_attendance_list,
    
    # Welfare Coordinator Views
    welfare_coordinator_dashboard,
    
    # Common Views
    support_staff_profile,
)

app_name = 'support_staff'

urlpatterns = [
    # ===== DEPARTMENT HEAD ROUTES =====
    path('dept-head/',
         dept_head_dashboard,
         name='dept_head_dashboard'),
    
    path('dept-head/staff/',
         dept_head_staff_list,
         name='dept_head_staff_list'),
    
    path('dept-head/staff/<int:staff_id>/',
         dept_head_staff_detail,
         name='dept_head_staff_detail'),
    
    # ===== SHIFT SUPERVISOR ROUTES =====
    path('shift-supervisor/',
         shift_supervisor_dashboard,
         name='shift_supervisor_dashboard'),
    
    path('shift-supervisor/attendance/',
         shift_attendance_list,
         name='shift_attendance_list'),
    
    # ===== WELFARE COORDINATOR ROUTES =====
    path('welfare/',
         welfare_coordinator_dashboard,
         name='welfare_coordinator_dashboard'),
    
    # ===== COMMON ROUTES =====
    path('profile/',
         support_staff_profile,
         name='support_staff_profile'),
]
