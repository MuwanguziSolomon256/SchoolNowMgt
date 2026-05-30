from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from SchoolNowMgt.models import StaffProfile, ClassGrade, Timetable
from .forms import TeacherProfileForm, TeacherQualificationForm


# NOTE: Ensure MEDIA_URL and MEDIA_ROOT are configured in settings.py
# for profile pictures to display correctly.
# Expected settings:
#   MEDIA_URL  = '/media/'
#   MEDIA_ROOT = BASE_DIR / 'media'


@login_required
def teacher_profile(request):
    """
    Display and edit teacher profile information.
    
    GET: Display teacher's profile with forms and read-only sections
         (assigned classes and timetable).
    POST: Process profile updates for personal info and qualifications.
    """
    # Fetch teacher's staff profile
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    
    # Fetch assigned classes
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff_profile
    ).select_related('school')
    
    # Fetch assigned timetable with optimizations
    my_timetable = Timetable.objects.filter(
        teacher=staff_profile
    ).select_related('subject', 'class_grade').order_by('day_of_week', 'start_time')
    
    if request.method == 'POST':
        # Bind forms to request data and files
        profile_form = TeacherProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        qualification_form = TeacherQualificationForm(
            request.POST,
            instance=staff_profile
        )
        
        # Validate and save both forms
        if profile_form.is_valid() and qualification_form.is_valid():
            profile_form.save()
            qualification_form.save()
            messages.success(request, 'Profile updated.')
            return redirect('teacher:profile')
        
        # If either form is invalid, re-render with errors
        context = {
            'profile_form': profile_form,
            'qualification_form': qualification_form,
            'staff_profile': staff_profile,
            'my_classes': my_classes,
            'my_timetable': my_timetable,
        }
        return render(request, 'teacher/profile.html', context)
    
    # GET request: instantiate forms with current data
    profile_form = TeacherProfileForm(instance=request.user)
    qualification_form = TeacherQualificationForm(instance=staff_profile)
    
    context = {
        'profile_form': profile_form,
        'qualification_form': qualification_form,
        'staff_profile': staff_profile,
        'my_classes': my_classes,
        'my_timetable': my_timetable,
    }
    
    return render(request, 'teacher/profile.html', context)
