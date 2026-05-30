from django.urls import path
from . import views, password_views
from user_profile.views import teacher_profile

app_name = 'teacher_auth'

urlpatterns = [
    path('register/', views.teacher_register, name='register'),
    path('login/', views.teacher_login, name='login'),
    path('logout/', views.teacher_logout, name='logout'),
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    path('profile/', teacher_profile, name='profile'),
    
    # Password reset URLs
    path('password-reset/', password_views.teacher_password_reset, name='password_reset'),
    path('password-reset/done/', password_views.teacher_password_reset_done, name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', password_views.teacher_password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', password_views.teacher_password_reset_complete, name='password_reset_complete'),
]
