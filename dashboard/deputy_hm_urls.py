"""
URL configuration for Deputy Headmaster Dashboard

Namespace: deputy_hm (accessed as 'deputy_hm:...')
Base path: /teacher/admin/deputy/
"""

from django.urls import path
from dashboard.deputy_hm_views import (
    deputy_hm_dashboard,
    support_staff_list, support_staff_edit,
    departments_list, department_create, department_edit, department_detail, department_delete,
    hostels_list, hostel_create, hostel_edit, hostel_detail, hostel_delete,
    shift_overview,
    facilities_overview,
    budget_overview,
)

app_name = 'deputy'

urlpatterns = [
    # Main Deputy HM Dashboard
    path('',
         deputy_hm_dashboard,
         name='dashboard'),
    
    # ===== SUPPORT STAFF MANAGEMENT =====
    path('staff/',
         support_staff_list,
         name='support_staff_list'),
    
    path('staff/<int:staff_id>/edit/',
         support_staff_edit,
         name='support_staff_edit'),
    
    # ===== DEPARTMENT MANAGEMENT =====
    path('departments/',
         departments_list,
         name='departments_list'),
    
    path('departments/create/',
         department_create,
         name='department_create'),
    
    path('departments/<int:department_id>/',
         department_detail,
         name='department_detail'),
    
    path('departments/<int:department_id>/edit/',
         department_edit,
         name='department_edit'),
    
    path('departments/<int:department_id>/delete/',
         department_delete,
         name='department_delete'),
    
    # ===== HOSTEL MANAGEMENT =====
    path('hostels/',
         hostels_list,
         name='hostels_list'),
    
    path('hostels/create/',
         hostel_create,
         name='hostel_create'),
    
    path('hostels/<int:hostel_id>/',
         hostel_detail,
         name='hostel_detail'),
    
    path('hostels/<int:hostel_id>/edit/',
         hostel_edit,
         name='hostel_edit'),
    
    path('hostels/<int:hostel_id>/delete/',
         hostel_delete,
         name='hostel_delete'),
    
    # ===== SHIFT MANAGEMENT =====
    path('shifts/',
         shift_overview,
         name='shift_overview'),
    
    # ===== FACILITIES =====
    path('facilities/',
         facilities_overview,
         name='facilities_overview'),
    
    # ===== BUDGET =====
    path('budget/',
         budget_overview,
         name='budget_overview'),
]
