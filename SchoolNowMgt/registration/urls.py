from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    path('teacher/', views.register_teacher, name='register_teacher'),
    path('admin/', views.register_admin, name='register_admin'),
    path('staff/', views.register_non_teaching_staff, name='register_staff'),
    path('parent/', views.register_parent, name='register_parent'),
    path('parent/login/', views.parent_login, name='parent_login'),
    path('support/login/', views.support_staff_login, name='support_login'),
    
    # Parent password reset URLs - TODO: Implement these views
    # path('parent/password-reset/', views.parent_password_reset, name='parent_password_reset'),
    # path('parent/password-reset/done/', views.parent_password_reset_done, name='parent_password_reset_done'),
    # path('parent/password-reset/<uidb64>/<token>/', views.parent_password_reset_confirm, name='parent_password_reset_confirm'),
    # path('parent/password-reset/complete/', views.parent_password_reset_complete, name='parent_password_reset_complete'),
    
    # Support staff password reset URLs - TODO: Implement these views
    # path('support/password-reset/', views.support_password_reset, name='support_password_reset'),
    # path('support/password-reset/done/', views.support_password_reset_done, name='support_password_reset_done'),
    # path('support/password-reset/<uidb64>/<token>/', views.support_password_reset_confirm, name='support_password_reset_confirm'),
    # path('support/password-reset/complete/', views.support_password_reset_complete, name='support_password_reset_complete'),
]
