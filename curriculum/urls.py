"""
URL routes for curriculum gradebook and grade entry views.

Routes:
  - /teacher/gradebook/ → Gradebook list view (class selection or grid)
  - /teacher/gradebook/<student_id>/ → Student transcript (detail view)
  - /teacher/gradebook/report/ → Class grade report and analytics
  - /teacher/gradebook/<student_id>/transcript/ → Formatted transcript for printing
  - /teacher/gradebook/export/ → Export gradebook to CSV
  - /teacher/grade/entry/uganda/ → Uganda national curriculum grade entry
  - /teacher/grade/entry/international/ → International curriculum grade entry
"""

from django.urls import path
from . import gradebook_views, views, international_views

app_name = 'curriculum'

urlpatterns = [
    # Gradebook views
    path('gradebook/', gradebook_views.gradebook_list, name='gradebook_list'),
    path('gradebook/<int:student_id>/', gradebook_views.gradebook_detail, name='gradebook_detail'),
    path('gradebook/report/', gradebook_views.grade_report, name='grade_report'),
    path('gradebook/<int:student_id>/transcript/', gradebook_views.student_transcript, name='student_transcript'),
    path('gradebook/export/', gradebook_views.export_grades, name='export_grades'),
    
    # Grade entry views
    path('grade/entry/uganda/', views.enter_grade_uganda, name='enter_grade_uganda'),
    path('grade/entry/international/', international_views.enter_grade_international, name='enter_grade_international'),
]
