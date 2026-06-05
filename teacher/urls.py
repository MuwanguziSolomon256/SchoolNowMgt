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
    student_search, quick_grade_entry, send_circular
)
from curriculum.views import enter_grade_uganda
from curriculum.international_views import enter_grade_international

app_name = 'teacher'

urlpatterns = [
    path('',             teacher_dashboard,    name='dashboard'),
    path('register/',    teacher_register,     name='register'),
    path('login/',       teacher_login,        name='login'),
    path('logout/',      teacher_logout,       name='logout'),
    path('profile/',     teacher_profile,      name='profile'),
    path('grades/uganda/',
         enter_grade_uganda,     name='enter_grade_uganda'),
    path('grades/international/',
         enter_grade_international,
         name='enter_grade_international'),

    # API Endpoints
    path('api/tasks/<int:task_id>/toggle/', toggle_task_status, name='toggle_task'),
    path('api/tasks/create/', create_task, name='create_task'),
    path('api/students/search/', student_search, name='student_search'),
    path('api/grades/quick-add/', quick_grade_entry, name='quick_grade_entry'),
    path('api/circulars/send/', send_circular, name='send_circular'),

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
