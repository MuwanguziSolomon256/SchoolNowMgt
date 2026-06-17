from django.urls import path
from . import views
from . import dashboard_views
from . import admin_shift_views

app_name = 'SchoolNowMgt'

urlpatterns = [
    path('', dashboard_views.dashboard, name='dashboard'),
    path('parent/', dashboard_views.parent_dashboard, name='parent_dashboard'),
    path('parent/messages/', dashboard_views.parent_message_inbox, name='parent_message_inbox'),
    path('parent/messages/<int:message_id>/', dashboard_views.parent_message_detail, name='parent_message_detail'),
    path('parent/api/message/send/', dashboard_views.parent_send_message_ajax, name='api_parent_message_send'),
    path('parent/api/message/<int:message_id>/mark-read/', dashboard_views.parent_mark_message_read_ajax, name='api_parent_message_mark_read'),
    path('parent/api/unread-count/', dashboard_views.get_parent_unread_count_ajax, name='api_parent_unread_count'),
    path('parent/children/', dashboard_views.parent_children_dashboard, name='parent_children_dashboard'),
    path('parent/academics/', dashboard_views.parent_academics_dashboard, name='parent_academics_dashboard'),
    path('parent/payments/', dashboard_views.parent_payments_dashboard, name='parent_payments_dashboard'),
    path('support-staff/', dashboard_views.support_staff_dashboard, name='support_staff_dashboard'),
    path('support-staff/profile/', dashboard_views.support_staff_profile_view, name='support_staff_profile'),
    path('support-staff/messages/', dashboard_views.support_staff_messages_dashboard, name='support_messages'),
    path('support-staff/payments/', dashboard_views.support_staff_payments_dashboard, name='support_payments'),
    path('support-staff/calendar/', dashboard_views.support_staff_calendar_dashboard, name='support_calendar'),
    path('support-staff/announcements/', dashboard_views.support_staff_announcements_dashboard, name='support_announcements'),
    path('support-staff/export/schedule/', dashboard_views.export_support_staff_schedule_csv, name='support_export_schedule'),
    path('support-staff/export/tasks/', dashboard_views.export_support_staff_tasks_csv, name='support_export_tasks'),
    path('enquiry/', views.enquiry_form, name='enquiry_form'),
    path('enquiry/success/', views.enquiry_success, name='enquiry_success'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance/done/', views.attendance_success, name='attendance_success'),
    path('logout/', views.custom_logout, name='custom_logout'),
    path('analytics/', views.live_analytics, name='live_analytics'),
    
    # Admin Mini-Dashboards (Phase 7)
    path('admin/students/', dashboard_views.admin_students_dashboard, name='admin_students'),
    path('admin/staff/', dashboard_views.admin_staff_dashboard, name='admin_staff'),
    path('admin/teachers/', dashboard_views.admin_teachers_dashboard, name='admin_teachers'),
    path('admin/support-staff/', dashboard_views.admin_support_staff_dashboard, name='admin_support_staff_dashboard'),
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
    path('api/staff-message/send/', dashboard_views.staff_send_message_ajax, name='api_staff_message_send'),
    path('api/message/send/', dashboard_views.send_message_ajax, name='api_message_send'),
    path('messages/inbox/', dashboard_views.message_inbox, name='message_inbox'),
    path('api/message/<int:message_id>/mark-read/', dashboard_views.mark_message_read_ajax, name='api_message_mark_read'),
    
    # Subject Management & Staff Editing AJAX Routes (Phase 2)
    path('api/subject/add/', dashboard_views.add_subject_ajax, name='api_subject_add'),
    path('api/subject/<int:subject_id>/edit/', dashboard_views.edit_subject_ajax, name='api_subject_edit'),
    path('api/subject/<int:subject_id>/delete/', dashboard_views.delete_subject_ajax, name='api_subject_delete'),
    path('api/subjects/', dashboard_views.get_subjects_ajax, name='api_subjects_list'),
    
    # Curriculum Management AJAX Routes (Phase 2+)
    path('api/curriculum/add/', dashboard_views.add_curriculum_ajax, name='api_curriculum_add'),
    path('api/curriculum/<int:curriculum_id>/edit/', dashboard_views.edit_curriculum_ajax, name='api_curriculum_edit'),
    path('api/curriculum/<int:curriculum_id>/delete/', dashboard_views.delete_curriculum_ajax, name='api_curriculum_delete'),
    path('api/curriculums/', dashboard_views.get_curriculums_ajax, name='api_curriculums_list'),
    
    path('api/teacher/<int:teacher_id>/edit/', dashboard_views.edit_teacher_ajax, name='api_teacher_edit'),
    path('api/teacher/<int:teacher_id>/delete/', dashboard_views.delete_teacher_ajax, name='api_teacher_delete'),
    path('api/support-staff/<int:staff_id>/edit/', dashboard_views.edit_support_staff_ajax, name='api_support_staff_edit'),
    path('api/support-staff/<int:staff_id>/delete/', dashboard_views.delete_support_staff_ajax, name='api_support_staff_delete'),
    
    # Admin Profile & Events Management (Phase 3)
    path('admin/profile/', dashboard_views.admin_profile_view, name='admin_profile'),
    path('admin/profile/edit/', dashboard_views.edit_admin_profile, name='edit_admin_profile'),
    path('admin/events/', dashboard_views.events_dashboard, name='events_dashboard'),
    path('admin/events/create/', dashboard_views.create_event, name='create_event'),
    path('admin/events/<int:event_id>/edit/', dashboard_views.edit_event, name='edit_event'),
    path('admin/events/<int:event_id>/delete/', dashboard_views.delete_event, name='delete_event'),
    
    # ===== SHIFT MANAGEMENT (ADMIN) =====
    path('admin/shifts/', admin_shift_views.shift_dashboard, name='admin_shift_dashboard'),
    path('admin/shifts/history/', admin_shift_views.shift_history, name='admin_shift_history'),
    path('admin/shifts/<int:attendance_id>/edit/', admin_shift_views.edit_shift_times, name='api_edit_shift'),
    path('admin/shifts/reports/', admin_shift_views.shift_report, name='admin_shift_report'),
]
