"""
URL configuration for Matron & Hostel Dashboards

Namespace: matron (accessed as 'matron:...')
Base path: /teacher/matron/

Includes routes for:
- Matron dashboard and hostel management
- Resident management and tracking
- Duty roster assignment
"""

from django.urls import path
from dashboard.matron_views import (
    matron_dashboard,
    hostels_list,
    hostel_detail,
    hostel_edit,
    residents_list,
    resident_detail,
    duty_roster,
)

app_name = 'matron'

urlpatterns = [
    # ===== MATRON DASHBOARD =====
    path('',
         matron_dashboard,
         name='dashboard'),
    
    # ===== HOSTEL MANAGEMENT =====
    path('hostels/',
         hostels_list,
         name='hostels_list'),
    
    path('hostels/<int:hostel_id>/',
         hostel_detail,
         name='hostel_detail'),
    
    path('hostels/<int:hostel_id>/edit/',
         hostel_edit,
         name='hostel_edit'),
    
    # ===== RESIDENT MANAGEMENT =====
    path('residents/',
         residents_list,
         name='residents_list'),
    
    path('residents/<int:student_id>/',
         resident_detail,
         name='resident_detail'),
    
    # ===== DUTY ROSTER =====
    path('duty-roster/',
         duty_roster,
         name='duty_roster'),
]
