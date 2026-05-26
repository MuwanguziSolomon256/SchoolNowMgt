from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('teacher/', views.register_teacher, name='register_teacher'),
    path('admin/', views.register_admin, name='register_admin'),
    path('staff/', views.register_non_teaching_staff, name='register_staff'),
    path('parent/', views.register_parent, name='register_parent'),
]
