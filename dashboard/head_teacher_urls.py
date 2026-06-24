"""
URL configuration for Head Teacher Admin Dashboard

Namespace: head_teacher (accessed as 'teacher:head_teacher:...')
Base path: /teacher/admin/head-teacher/

Includes routes for:
- Head Teacher dashboard and academic oversight
- School-wide timetable management
- Staff oversight and performance tracking
"""

from django.urls import path
from . import head_teacher_views

app_name = 'head_teacher'

urlpatterns = [
    # ===== HEAD TEACHER DASHBOARD =====
    path('',
         head_teacher_views.head_teacher_dashboard,
         name='dashboard'),
    
    # ===== ACADEMIC OVERSIGHT =====
    path('academic-performance/',
         head_teacher_views.academic_performance,
         name='academic_performance'),
    
    # ===== STAFF OVERSIGHT =====
    path('staff/',
         head_teacher_views.staff_oversight,
         name='staff_oversight'),
    
    # ===== TIMETABLE MANAGEMENT =====
    path('timetable/',
         head_teacher_views.school_timetable,
         name='school_timetable'),
]
