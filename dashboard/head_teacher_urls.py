"""
URL configuration for Head Teacher Admin Dashboard

Namespace: head_teacher (accessed as 'teacher:head_teacher:...')
Base path: /teacher/admin/head-teacher/

Includes routes for:
- Head Teacher dashboard and academic oversight
- School-wide timetable management
- Staff oversight and performance tracking
- Headmaster Institutional Pulse dashboard
"""

from django.urls import path
from . import head_teacher_views

app_name = 'head_teacher'

urlpatterns = [
    # ===== HEADMASTER INSTITUTIONAL PULSE DASHBOARD (DEFAULT) =====
    path('',
         head_teacher_views.headmaster_dashboard,
         name='dashboard'),
    
    # ===== HEADMASTER INSTITUTIONAL PULSE DASHBOARD (LEGACY URL) =====
    path('headmaster/',
         head_teacher_views.headmaster_dashboard,
         name='headmaster_dashboard'),
    
    path('headmaster/create-event/',
         head_teacher_views.create_event,
         name='create_event'),

    path('headmaster/event/<int:event_id>/',
         head_teacher_views.get_event,
         name='get_event'),

    # Per-section dashboard routes - each nav item has its own URL but renders the same headmaster dashboard
    path('financials/',
         head_teacher_views.financials_dashboard,
         name='financials'),

    path('enrollment/',
         head_teacher_views.enrollment_dashboard,
         name='enrollment'),

    path('calendar/',
         head_teacher_views.calendar_dashboard,
         name='calendar'),
    
    path('headmaster/event/<int:event_id>/update/',
         head_teacher_views.update_event,
         name='update_event'),
    
    path('headmaster/event/<int:event_id>/delete/',
         head_teacher_views.delete_event,
         name='delete_event'),
    
    path('headmaster/chart-data/',
         head_teacher_views.get_chart_data,
         name='get_chart_data'),
    
    path('headmaster/export-report/',
         head_teacher_views.export_dashboard_report,
         name='export_report'),
    
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
