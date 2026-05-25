from django.urls import path
from . import views
from . import dashboard_views

app_name = 'SchoolNowMgt'

urlpatterns = [
    path('', dashboard_views.dashboard, name='dashboard'),
    path('enquiry/', views.enquiry_form, name='enquiry_form'),
    path('enquiry/success/', views.enquiry_success, name='enquiry_success'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance/done/', views.attendance_success, name='attendance_success'),
    path('logout/', views.custom_logout, name='custom_logout'),
]
