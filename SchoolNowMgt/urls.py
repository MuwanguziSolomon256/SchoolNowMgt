from django.urls import path
from . import views
from . import dashboard_views

app_name = 'SchoolNowMgt'

urlpatterns = [
    path('', dashboard_views.dashboard, name='dashboard'),
    path('parent/', dashboard_views.parent_dashboard, name='parent_dashboard'),
    path('parent/messages/', dashboard_views.parent_message_inbox, name='parent_message_inbox'),
    path('parent/messages/<int:message_id>/', dashboard_views.parent_message_detail, name='parent_message_detail'),
    path('parent/api/message/send/', dashboard_views.parent_send_message_ajax, name='api_parent_message_send'),
    path('parent/api/message/<int:message_id>/mark-read/', dashboard_views.parent_mark_message_read_ajax, name='api_parent_message_mark_read'),
    path('parent/api/unread-count/', dashboard_views.get_parent_unread_count_ajax, name='api_parent_unread_count'),
    path('support-staff/', dashboard_views.support_staff_dashboard, name='support_staff_dashboard'),
    path('enquiry/', views.enquiry_form, name='enquiry_form'),
    path('enquiry/success/', views.enquiry_success, name='enquiry_success'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance/done/', views.attendance_success, name='attendance_success'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('analytics/', views.live_analytics, name='live_analytics'),
    
    # Admin Mini-Dashboards (Phase 7)
    path('admin/students/', dashboard_views.admin_students_dashboard, name='admin_students'),
    path('admin/staff/', dashboard_views.admin_staff_dashboard, name='admin_staff'),
    path('admin/communication/', dashboard_views.admin_communication_dashboard, name='admin_communication'),
    path('admin/finance/', dashboard_views.admin_finance_dashboard, name='admin_finance'),
    path('admin/reports/', dashboard_views.admin_reports_dashboard, name='admin_reports'),
    
    # CSV Export Endpoints (Phase 1.5)
    path('export/students/', dashboard_views.export_students_csv, name='export_students'),
    path('export/staff/', dashboard_views.export_staff_csv, name='export_staff'),
    path('export/finance/', dashboard_views.export_finance_csv, name='export_finance'),
    path('export/reports/', dashboard_views.export_reports_csv, name='export_reports'),
    
    # Admin Onboarding & Messaging API Routes (Phase 6)
    path('api/staff/onboard/', dashboard_views.onboard_staff_ajax, name='api_staff_onboard'),
    path('api/staff/bulk-onboard/', dashboard_views.bulk_onboard_staff_ajax, name='api_staff_bulk_onboard'),
    path('api/staff/reset-password/', dashboard_views.reset_staff_password_ajax, name='api_staff_reset_password'),
    path('api/student/onboard/', dashboard_views.onboard_student_ajax, name='api_student_onboard'),
    path('api/student/bulk-onboard/', dashboard_views.bulk_onboard_student_ajax, name='api_student_bulk_onboard'),
    path('api/message/send/', dashboard_views.send_message_ajax, name='api_message_send'),
    path('messages/inbox/', dashboard_views.message_inbox, name='message_inbox'),
    path('api/message/<int:message_id>/mark-read/', dashboard_views.mark_message_read_ajax, name='api_message_mark_read'),
    
    # Admin Profile & Events Management (Phase 3)
    path('admin/profile/', dashboard_views.admin_profile_view, name='admin_profile'),
    path('admin/profile/edit/', dashboard_views.edit_admin_profile, name='edit_admin_profile'),
    path('admin/events/', dashboard_views.events_dashboard, name='events_dashboard'),
    path('admin/events/create/', dashboard_views.create_event, name='create_event'),
    path('admin/events/<int:event_id>/edit/', dashboard_views.edit_event, name='edit_event'),
    path('admin/events/<int:event_id>/delete/', dashboard_views.delete_event, name='delete_event'),
]
