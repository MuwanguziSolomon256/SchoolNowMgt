from django.urls import path
from . import views

app_name = 'user_profile'

urlpatterns = [
    # Parent profile edit view
    path('edit/', views.edit_profile, name='edit_profile'),
    
    # Teacher profile view
    path('teacher/', views.teacher_profile, name='teacher_profile'),
    
    # Support Staff profile views
    path('support-staff/', views.support_staff_profile_view, name='support_staff_profile'),
    path('support-staff/edit/', views.support_staff_edit_profile, name='support_staff_edit_profile'),
]
