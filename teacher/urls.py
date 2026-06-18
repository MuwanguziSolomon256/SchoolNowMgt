from django.urls import path
from teacher_auth.views import teacher_login, teacher_logout, teacher_register
from teacher_auth.password_views import (
    teacher_password_reset,
    teacher_password_reset_done,
    teacher_password_reset_confirm,
    teacher_password_reset_complete,
)
from user_profile.views import teacher_profile
from dashboard.teacher_views import (
    teacher_dashboard, toggle_task_status, create_task,
    student_search, quick_grade_entry, send_circular,
    teacher_students_list, teacher_lessons_list,
    export_teacher_schedule_csv, export_teacher_attendance_csv,
    get_student_info_ajax
)
from dashboard.teacher_sub_views import (
    # Grades sub-dashboard
    grades_dashboard, grade_entry_interface, grade_statistics,
    grade_export, grade_history,
    # Communication sub-dashboard
    message_inbox, message_detail, send_message_ajax, mark_message_read_ajax,
    # Attendances sub-dashboard
    attendance_marking, attendance_history, mark_attendance_ajax,
    # Gradebook reference
    gradebook_reference, grade_lookup_ajax,
)
from curriculum.views import enter_grade_uganda
from curriculum.international_views import enter_grade_international
from curriculum.gradebook_views import (
    gradebook_list, gradebook_detail, grade_report,
    student_transcript, export_grades
)
from teacher.shift_views import (
    clock_in, clock_out, break_start, break_end, shift_status
)

app_name = 'teacher'

urlpatterns = [
    path('',             teacher_dashboard,    name='dashboard'),
    path('register/',    teacher_register,     name='register'),
    path('login/',       teacher_login,        name='login'),
    path('logout/',      teacher_logout,       name='logout'),
    path('profile/',     teacher_profile,      name='profile'),
    
    # New navigation routes (Phase 3)
    path('students/',    teacher_students_list, name='students'),
    path('lessons/',     teacher_lessons_list,  name='lessons'),
    
    # ===== GRADES SUB-DASHBOARD =====
    path('grades/',                 grades_dashboard,        name='grades_dashboard'),
    path('grades/entry/',           grade_entry_interface,   name='grade_entry'),
    path('grades/statistics/',      grade_statistics,        name='grade_statistics'),
    path('grades/export/',          grade_export,            name='grade_export'),
    path('grades/history/',         grade_history,           name='grade_history'),
    
    # ===== COMMUNICATION SUB-DASHBOARD =====
    path('communication/',                message_inbox,              name='message_inbox'),
    path('communication/message/<int:message_id>/',  message_detail,     name='message_detail'),
    path('api/communication/send/',       send_message_ajax,          name='send_message_ajax'),
    path('api/communication/message/<int:message_id>/read/',  mark_message_read_ajax,  name='mark_message_read'),
    
    # ===== ATTENDANCES SUB-DASHBOARD =====
    path('attendances/',            attendance_marking,       name='attendance_marking'),
    path('attendances/history/',    attendance_history,       name='attendance_history'),
    path('api/attendances/mark/',   mark_attendance_ajax,     name='mark_attendance_ajax'),
    
    # ===== GRADEBOOK (NEW CURRICULUM-AWARE VIEWS) =====
    path('gradebook/',              gradebook_list,         name='gradebook_list'),
    path('gradebook/<int:student_id>/',  gradebook_detail,  name='gradebook_detail'),
    path('gradebook/report/',       grade_report,           name='grade_report'),
    path('gradebook/<int:student_id>/transcript/',  student_transcript,  name='student_transcript'),
    path('gradebook/export/',       export_grades,          name='export_grades'),
    
    # ===== LEGACY GRADE ENTRY (Keeping for backward compatibility) =====
    path('grades/uganda/',          enter_grade_uganda,       name='enter_grade_uganda'),
    path('grades/international/',   enter_grade_international, name='enter_grade_international'),

    # API Endpoints
    path('api/tasks/<int:task_id>/toggle/', toggle_task_status, name='toggle_task'),
    path('api/tasks/create/', create_task, name='create_task'),
    path('api/students/search/', student_search, name='student_search'),
    path('api/student/<int:student_id>/', get_student_info_ajax, name='get_student_info'),
    path('api/grades/quick-add/', quick_grade_entry, name='quick_grade_entry'),
    path('api/circulars/send/', send_circular, name='send_circular'),

    # ===== SHIFT MANAGEMENT API =====
    path('api/shift/clock-in/', clock_in, name='api_clock_in'),
    path('api/shift/clock-out/', clock_out, name='api_clock_out'),
    path('api/shift/break-start/', break_start, name='api_break_start'),
    path('api/shift/break-end/', break_end, name='api_break_end'),
    path('api/shift/status/', shift_status, name='api_shift_status'),

    # ===== EXPORT ENDPOINTS =====
    path('export/schedule/', export_teacher_schedule_csv, name='export_schedule'),
    path('export/attendance/', export_teacher_attendance_csv, name='export_attendance'),

    path('password/reset/',
         teacher_password_reset,
         name='password_reset'),
    path('password/reset/sent/',
         teacher_password_reset_done,
         name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/',
         teacher_password_reset_confirm,
         name='password_reset_confirm'),
    path('password/reset/complete/',
         teacher_password_reset_complete,
         name='password_reset_complete'),
]
