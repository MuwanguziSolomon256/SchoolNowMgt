"""
Password reset views for Parent and Support Staff roles.

Similar structure to teacher_auth/password_views.py but role-specific.
"""

from django.contrib.auth.views import (
    PasswordResetView as DjangoPasswordResetView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
)
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import get_user_model

from .forms import ParentPasswordResetForm, SupportStaffPasswordResetForm

User = get_user_model()


# ═════════════════════════════════════════════════════════════════════════════
# PARENT PASSWORD RESET
# ═════════════════════════════════════════════════════════════════════════════


class ParentPasswordResetView(DjangoPasswordResetView):
    """Parent-specific password reset view."""
    form_class = ParentPasswordResetForm
    template_name = 'registration/password_reset_request.html'
    email_template_name = 'registration/password_reset_email_parent.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('registration:parent_password_reset_done')


class ParentPasswordResetDoneView(DjangoPasswordResetDoneView):
    """Confirmation page after parent submits password reset form."""
    template_name = 'registration/password_reset_sent.html'


class ParentPasswordResetConfirmView(DjangoPasswordResetConfirmView):
    """Parent sets new password via reset token."""
    form_class = SetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('registration:parent_password_reset_complete')


class ParentPasswordResetCompleteView(DjangoPasswordResetCompleteView):
    """Success page after parent resets password."""
    template_name = 'registration/password_reset_complete.html'


# View wrappers (for backward compatibility with function-based views)
parent_password_reset = ParentPasswordResetView.as_view()
parent_password_reset_done = ParentPasswordResetDoneView.as_view()
parent_password_reset_confirm = ParentPasswordResetConfirmView.as_view()
parent_password_reset_complete = ParentPasswordResetCompleteView.as_view()


# ═════════════════════════════════════════════════════════════════════════════
# SUPPORT STAFF PASSWORD RESET
# ═════════════════════════════════════════════════════════════════════════════


class SupportPasswordResetView(DjangoPasswordResetView):
    """Support staff-specific password reset view."""
    form_class = SupportStaffPasswordResetForm
    template_name = 'registration/password_reset_request.html'
    email_template_name = 'registration/password_reset_email_support.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('registration:support_password_reset_done')


class SupportPasswordResetDoneView(DjangoPasswordResetDoneView):
    """Confirmation page after support staff submits password reset form."""
    template_name = 'registration/password_reset_sent.html'


class SupportPasswordResetConfirmView(DjangoPasswordResetConfirmView):
    """Support staff sets new password via reset token."""
    form_class = SetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('registration:support_password_reset_complete')


class SupportPasswordResetCompleteView(DjangoPasswordResetCompleteView):
    """Success page after support staff resets password."""
    template_name = 'registration/password_reset_complete.html'


# View wrappers (for backward compatibility with function-based views)
support_password_reset = SupportPasswordResetView.as_view()
support_password_reset_done = SupportPasswordResetDoneView.as_view()
support_password_reset_confirm = SupportPasswordResetConfirmView.as_view()
support_password_reset_complete = SupportPasswordResetCompleteView.as_view()
