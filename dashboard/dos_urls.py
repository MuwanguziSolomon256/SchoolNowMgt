"""
URL configuration for Director of Studies (DOS) Dashboard

Namespace: dos (accessed as 'dos:...')
Base path: /teacher/admin/dos/
"""

from django.urls import path
from dashboard.dos_views import (
    dos_dashboard,
    timetable_list, timetable_create, timetable_edit, timetable_delete,
    class_teacher_assignments_list,
    class_teacher_assignment_create, class_teacher_assignment_edit,
    class_teacher_assignment_delete,
    departments_overview,
    academic_reports,
)
from dashboard.dos_department_views import (
    departments_list, department_create, department_edit, department_detail,
    department_delete, assign_department_head,
)

app_name = 'dos'

urlpatterns = [
    # Main DOS Dashboard
    path('',
         dos_dashboard,
         name='dashboard'),
    
    # ===== TIMETABLE MANAGEMENT =====
    path('timetable/',
         timetable_list,
         name='timetable_list'),
    
    path('timetable/create/',
         timetable_create,
         name='timetable_create'),
    
    path('timetable/<int:timetable_id>/edit/',
         timetable_edit,
         name='timetable_edit'),
    
    path('timetable/<int:timetable_id>/delete/',
         timetable_delete,
         name='timetable_delete'),
    
    # ===== CLASS TEACHER ASSIGNMENTS =====
    path('class-teachers/',
         class_teacher_assignments_list,
         name='class_teacher_assignments_list'),
    
    path('class-teachers/create/',
         class_teacher_assignment_create,
         name='class_teacher_assignment_create'),
    
    path('class-teachers/<int:assignment_id>/edit/',
         class_teacher_assignment_edit,
         name='class_teacher_assignment_edit'),
    
    path('class-teachers/<int:assignment_id>/delete/',
         class_teacher_assignment_delete,
         name='class_teacher_assignment_delete'),
    
    # ===== ACADEMIC DEPARTMENTS MANAGEMENT =====
    path('departments/',
         departments_list,
         name='departments_list'),
    
    path('departments/create/',
         department_create,
         name='department_create'),
    
    path('departments/<int:dept_id>/edit/',
         department_edit,
         name='department_edit'),
    
    path('departments/<int:dept_id>/',
         department_detail,
         name='department_detail'),
    
    path('departments/<int:dept_id>/delete/',
         department_delete,
         name='department_delete'),
    
    path('departments/<int:dept_id>/assign-head/',
         assign_department_head,
         name='assign_department_head'),
    
    # ===== LEGACY DEPARTMENTS OVERVIEW =====
    path('departments-overview/',
         departments_overview,
         name='departments_overview'),
    
    # ===== REPORTING =====
    path('reports/',
         academic_reports,
         name='academic_reports'),
]
