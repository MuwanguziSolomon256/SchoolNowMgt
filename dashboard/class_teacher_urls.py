"""
Class Teacher Dashboard URLs
Routes for class management, student tracking, grade management, and parent communication
"""

from django.urls import path
from . import class_teacher_views

app_name = 'class_teacher'

urlpatterns = [
    # Class Overview
    path('', class_teacher_views.class_dashboard, name='dashboard'),
    
    # Students Management
    path('students/', class_teacher_views.students_list, name='students_list'),
    path('students/<int:student_id>/', class_teacher_views.student_detail, name='student_detail'),
    
    # Grades Management
    path('grades/', class_teacher_views.grades_management, name='grades'),
    
    # Attendance Management
    path('attendance/', class_teacher_views.attendance_management, name='attendance'),
    
    # Class Performance
    path('performance/', class_teacher_views.class_performance, name='performance'),
    
    # Parent Communications
    path('parents/', class_teacher_views.parent_communications, name='parents'),
]
