"""
URL configuration for schoolmgmt_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.http import require_http_methods

# Import home view
from SchoolNowMgt.views import home


@require_http_methods(["GET", "HEAD"])
def health_check(request):
    """Simple health check endpoint that doesn't access the database."""
    return HttpResponse("OK", status=200)


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls', namespace='auth')),
    path('accounts/', include([
        path('teacher/', include('teacher_auth.urls', namespace='teacher_auth')),
        path('', include('django.contrib.auth.urls')),
        # Allauth URLs for social authentication
        path('', include('allauth.urls')),
    ])),
    path('teacher/', include('teacher.urls', namespace='teacher')),
    path('profile/', include('user_profile.urls', namespace='user_profile')),
    path('school/', include('SchoolNowMgt.urls')),
    path('register/', include('SchoolNowMgt.registration.urls', namespace='registration')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
