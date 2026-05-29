from django.urls import path
from . import views
from . import dashboard_views

app_name = 'SchoolNowMgt'

urlpatterns = [
    path('', dashboard_views.dashboard, name='dashboard'),
    path('parent/', dashboard_views.parent_dashboard, name='parent_dashboard'),
    path('support-staff/', dashboard_views.support_staff_dashboard, name='support_staff_dashboard'),
    path('enquiry/', views.enquiry_form, name='enquiry_form'),
    path('enquiry/success/', views.enquiry_success, name='enquiry_success'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance/done/', views.attendance_success, name='attendance_success'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('analytics/', views.live_analytics, name='live_analytics'),
]
