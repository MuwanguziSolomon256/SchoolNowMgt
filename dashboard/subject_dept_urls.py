"""
Subject Department Head Dashboard URLs
Routes for department management, teacher oversight, subject management, and performance tracking
"""

from django.urls import path
from . import subject_dept_views

app_name = 'subject_dept'

urlpatterns = [
    # Department Overview
    path('', subject_dept_views.dept_dashboard, name='dashboard'),
    
    # Teachers Management
    path('teachers/', subject_dept_views.teachers_list, name='teachers_list'),
    path('teachers/<int:teacher_id>/', subject_dept_views.teacher_detail, name='teacher_detail'),
    
    # Subjects Management
    path('subjects/', subject_dept_views.subjects_list, name='subjects_list'),
    path('subjects/<int:subject_id>/', subject_dept_views.subject_detail, name='subject_detail'),
    
    # Classes Management
    path('classes/', subject_dept_views.classes_list, name='classes_list'),
    
    # Timetable Overview
    path('timetable/', subject_dept_views.timetable_overview, name='timetable'),
    
    # Performance Report
    path('performance/', subject_dept_views.performance_report, name='performance'),
]
