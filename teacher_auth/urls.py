from django.urls import path
from . import views
from profile.views import teacher_profile

app_name = 'teacher_auth'

urlpatterns = [
    path('register/', views.teacher_register, name='register'),
    path('login/', views.teacher_login, name='login'),
    path('logout/', views.teacher_logout, name='logout'),
    path('dashboard/', views.teacher_dashboard, name='dashboard'),
    path('profile/', teacher_profile, name='profile'),
]
