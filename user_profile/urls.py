from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    # Parent profile edit view
    path('edit/', views.edit_profile, name='edit_profile'),
    
    # Teacher profile view
    path('teacher/', views.teacher_profile, name='teacher_profile'),
]
