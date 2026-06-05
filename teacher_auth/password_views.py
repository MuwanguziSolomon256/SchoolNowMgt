from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy

from .password_forms import TeacherPasswordResetForm, TeacherSetPasswordForm


# ============================================================================
# SETTINGS REMINDER
# ============================================================================
# Add the following to your Django settings.py for email functionality:
#
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# (In development, use: 'django.core.mail.backends.console.EmailBackend')
#
# DEFAULT_FROM_EMAIL = 'School Name <noreply@yourschool.com>'
#
# PASSWORD_RESET_TIMEOUT = 86400  # 24 hours (Django default)
#
# For Gmail SMTP (example):
#   EMAIL_HOST = 'smtp.gmail.com'
#   EMAIL_PORT = 587
#   EMAIL_USE_TLS = True
#   EMAIL_HOST_USER = 'your-email@gmail.com'
#   EMAIL_HOST_PASSWORD = 'your-app-password'
# ============================================================================


# ============================================================================
# URL WIRING REFERENCE
# ============================================================================
# Add these patterns to teacher_auth/urls.py:
#
# from django.urls import path
# from . import password_views
#
# app_name = 'teacher'
#
# urlpatterns = [
#     # ... existing login/logout patterns ...
#     path('password-reset/', password_views.teacher_password_reset,
#          name='password_reset'),
#     path('password-reset/done/', password_views.teacher_password_reset_done,
#          name='password_reset_done'),
#     path('password-reset/<uidb64>/<token>/', password_views.teacher_password_reset_confirm,
#          name='password_reset_confirm'),
#     path('password-reset/complete/', password_views.teacher_password_reset_complete,
#          name='password_reset_complete'),
# ]
# ============================================================================


teacher_password_reset = PasswordResetView.as_view(
    form_class=TeacherPasswordResetForm,
    template_name='teacher/password_reset_request.html',
    email_template_name='teacher/email/password_reset_email.txt',
    subject_template_name='teacher/email/password_reset_subject.txt',
    success_url=reverse_lazy('teacher:password_reset_done'),
)


teacher_password_reset_done = PasswordResetDoneView.as_view(
    template_name='teacher/password_reset_sent.html',
)


teacher_password_reset_confirm = PasswordResetConfirmView.as_view(
    form_class=TeacherSetPasswordForm,
    template_name='teacher/password_reset_confirm.html',
    success_url=reverse_lazy('teacher:password_reset_complete'),
)


teacher_password_reset_complete = PasswordResetCompleteView.as_view(
    template_name='teacher/password_reset_complete.html',
)
