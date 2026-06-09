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
    
    # Admin Onboarding & Messaging API Routes (Phase 6)
    path('api/staff/onboard/', dashboard_views.onboard_staff_ajax, name='api_staff_onboard'),
    path('api/staff/bulk-onboard/', dashboard_views.bulk_onboard_staff_ajax, name='api_staff_bulk_onboard'),
    path('api/staff/reset-password/', dashboard_views.reset_staff_password_ajax, name='api_staff_reset_password'),
    path('api/student/onboard/', dashboard_views.onboard_student_ajax, name='api_student_onboard'),
    path('api/student/bulk-onboard/', dashboard_views.bulk_onboard_student_ajax, name='api_student_bulk_onboard'),
    path('api/message/send/', dashboard_views.send_message_ajax, name='api_message_send'),
    path('messages/inbox/', dashboard_views.message_inbox, name='message_inbox'),
    path('api/message/<int:message_id>/mark-read/', dashboard_views.mark_message_read_ajax, name='api_message_mark_read'),
]
