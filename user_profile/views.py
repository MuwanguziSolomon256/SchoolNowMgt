from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from SchoolNowMgt.models import StaffProfile, ClassGrade, Timetable, CustomUser
from .forms import TeacherProfileForm, TeacherQualificationForm, ParentProfileForm, SupportStaffProfileForm, SupportStaffDetailsForm


# NOTE: Ensure MEDIA_URL and MEDIA_ROOT are configured in settings.py
# for profile pictures to display correctly.
# Expected settings:
#   MEDIA_URL  = '/media/'
#   MEDIA_ROOT = BASE_DIR / 'media'


@login_required
def teacher_profile(request):
    """
    Display and edit teacher profile information.
    
    GET: Display teacher's profile edit form.
    POST: Process profile updates for personal info.
    """
    # Fetch teacher's staff profile
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        # Bind form to request data and files
        profile_form = TeacherProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        
        # Validate and save form
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('teacher:profile')
        
        # If form is invalid, re-render with errors
        context = {
            'profile_form': profile_form,
            'staff_profile': staff_profile,
        }
        return render(request, 'teacher/profile.html', context)
    
    # GET request: instantiate form with current data
    profile_form = TeacherProfileForm(instance=request.user)
    
    context = {
        'profile_form': profile_form,
        'staff_profile': staff_profile,
    }
    
    return render(request, 'teacher/profile.html', context)


@login_required
def edit_profile(request):
    """
    Display and edit parent profile information.
    
    GET: Display parent's profile edit form with current information.
    POST: Process profile updates (name, email, phone, profile picture).
    
    This view is accessible to parent users from the dashboard settings icon.
    """
    # Restrict access to parents only
    if request.user.role != 'parent':
        messages.error(request, 'This page is only accessible to parents.')
        return redirect('SchoolNowMgt:parent_dashboard')
    
    if request.method == 'POST':
        # Bind form to request data and files
        form = ParentProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        
        # Validate and save form
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('SchoolNowMgt:parent_dashboard')
        
        # If form is invalid, re-render with errors
        context = {'form': form}
        return render(request, 'SchoolNowMgt/parent_profile_edit.html', context)
    
    # GET request: instantiate form with current data
    form = ParentProfileForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'SchoolNowMgt/parent_profile_edit.html', context)


@login_required
def support_staff_profile_view(request):
    """
    Display support staff profile information (read-only view).
    
    Shows: basic info, position, department, qualifications, emergency contact, bank details (masked)
    """
    # Restrict access to support staff only
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'This page is only accessible to support staff.')
        return redirect('SchoolNowMgt:dashboard')
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    context = {
        'staff_profile': staff_profile,
        'user': request.user,
    }
    
    return render(request, 'SchoolNowMgt/support_staff_profile.html', context)


@login_required
def support_staff_edit_profile(request):
    """
    Display and edit support staff profile information.
    
    GET: Display support staff's profile edit forms with current information.
    POST: Process profile updates (name, phone, profile picture, emergency contact, bank details).
    
    This view is accessible to support staff users from the dashboard.
    """
    # Restrict access to support staff only
    if request.user.role != 'non_teaching_staff':
        messages.error(request, 'This page is only accessible to support staff.')
        return redirect('SchoolNowMgt:dashboard')
    
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        # Bind forms to request data and files
        profile_form = SupportStaffProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        details_form = SupportStaffDetailsForm(
            request.POST,
            instance=staff_profile
        )
        
        # Validate and save both forms
        if profile_form.is_valid() and details_form.is_valid():
            profile_form.save()
            details_form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_profile:support_staff_profile')
        
        # If either form is invalid, re-render with errors
        context = {
            'profile_form': profile_form,
            'details_form': details_form,
            'staff_profile': staff_profile,
        }
        return render(request, 'SchoolNowMgt/support_staff_profile_edit.html', context)
    
    # GET request: instantiate forms with current data
    profile_form = SupportStaffProfileForm(instance=request.user)
    details_form = SupportStaffDetailsForm(instance=staff_profile)
    
    context = {
        'profile_form': profile_form,
        'details_form': details_form,
        'staff_profile': staff_profile,
    }
    
    return render(request, 'SchoolNowMgt/support_staff_profile_edit.html', context)

