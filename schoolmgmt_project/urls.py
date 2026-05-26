"""
URL configuration for schoolmgmt_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# Import home view
from SchoolNowMgt.views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('teacher/', include('teacher.urls', namespace='teacher')),
    path('accounts/', include([
        path('teacher/', include('teacher_auth.urls', namespace='teacher_auth')),
        path('', include('django.contrib.auth.urls')),
    ])),
    path('school/', include('SchoolNowMgt.urls')),
    path('register/', include('SchoolNowMgt.registration.urls', namespace='registration')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
