from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Unified entry points - PRIMARY ROUTES
    path('login/', views.unified_login, name='unified_login'),
    path('register/', views.unified_register, name='unified_register'),
    
    # Parent-specific registration
    path('parent/register/', views.parent_register, name='parent_register'),
    
    # Alternate names for backward compatibility
    path('', views.unified_login, name='login'),
    
    # Role routing - redirects to unified pages
    path('login/<str:role>/', views.login_role, name='login_role'),
    path('register/<str:role>/', views.register_role, name='register_role'),
]
