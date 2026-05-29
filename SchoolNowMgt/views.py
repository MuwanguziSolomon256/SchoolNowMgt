from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.db import ProgrammingError
from datetime import datetime

from .models import ClassGrade, Student, StudentAttendance, Enquiry, School
from .forms import EnquiryForm, AttendanceMarkingForm


def get_school_safe():
    """
    Safely get the first school from the database.
    Returns None if the table doesn't exist yet (during initial deployment).
    """
    try:
        return School.objects.first()
    except ProgrammingError:
        # School table doesn't exist yet - migrations haven't run
        return None


def home(request):
    """
    Landing page showing the system and role-based entry points.
    Accessible to both authenticated and unauthenticated users.
    """
    school = get_school_safe()
    context = {
        'school': school,
    }
    return render(request, 'SchoolNowMgt/home.html', context)


def enquiry_form(request):
    """
    Public view for school enquiry form.
    GET: Display the enquiry form with school name.
    POST: Save enquiry and redirect to success page.
    """
    school = get_school_safe()

    if request.method == 'POST':
        form = EnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save(commit=False)
            enquiry.school = school
            enquiry.status = 'new'
            enquiry.save()
            return redirect('SchoolNowMgt:enquiry_success')
    else:
        form = EnquiryForm()

    context = {
        'form': form,
        'school': school,
    }
    return render(request, 'SchoolNowMgt/enquiry_form.html', context)


def enquiry_success(request):
    """
    Public view showing enquiry submission success message.
    """
    return render(request, 'SchoolNowMgt/enquiry_success.html')


@login_required
def mark_attendance(request):
    """
    Staff view for marking student attendance.
    Two-step process:
      Step 1 (GET or POST without student_ids): Select class and date, load students.
      Step 2 (POST with student_ids): Save attendance records and redirect.
    """
    if request.method == 'POST':
        # Check if this is step 2 (student_ids flag present)
        if 'student_ids' in request.POST:
            # Step 2: Save attendance records
            selected_date_str = request.POST.get('selected_date')
            class_grade_id = request.POST.get('class_grade_id')

            # Parse date
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            class_grade = get_object_or_404(ClassGrade, pk=class_grade_id)

            # Get all active students in this class
            students = Student.objects.filter(
                class_grade=class_grade,
                status='active'
            ).order_by('last_name')

            # Save attendance for each student
            for student in students:
                status = request.POST.get(f'status_{student.pk}', 'absent')
                StudentAttendance.objects.update_or_create(
                    student=student,
                    date=selected_date,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'synced': True,
                    }
                )

            return redirect('SchoolNowMgt:attendance_success')

        else:
            # Step 1: Form submitted with class and date, load students
            form = AttendanceMarkingForm(request.POST)
            if form.is_valid():
                class_grade = form.cleaned_data['class_grade']
                selected_date = form.cleaned_data['date']

                # Get active students for the selected class
                students = Student.objects.filter(
                    class_grade=class_grade,
                    status='active'
                ).order_by('last_name')

                context = {
                    'form': form,
                    'students': students,
                    'selected_date': selected_date,
                }
                return render(request, 'SchoolNowMgt/mark_attendance.html', context)
    else:
        # GET request: render empty form
        form = AttendanceMarkingForm()

    context = {
        'form': form,
        'students': None,
    }
    return render(request, 'SchoolNowMgt/mark_attendance.html', context)


@login_required
def attendance_success(request):
    """
    Staff view showing attendance submission success message.
    """
    return render(request, 'SchoolNowMgt/attendance_success.html')


def custom_logout(request):
    """
    Custom logout view that handles both GET (confirmation) and POST (actual logout).
    GET: Display logout confirmation page with a POST form.
    POST: Log out the user and redirect to login page.
    """
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    
    # GET: Show logout confirmation page
    return render(request, 'registration/logout_confirm.html')


@login_required(login_url='SchoolNowMgt:login')
def live_analytics(request):
    """
    Live analytics dashboard showing key performance indicators.
    Requires admin/staff authentication.
    """
    from django.db.models import Count, Q, Avg
    from decimal import Decimal
    from SchoolNowMgt.models import RetentionAlert, CustomUser
    
    school = get_school_safe()
    
    # Get basic statistics
    total_students = Student.objects.filter(status='active').count()
    total_teachers = CustomUser.objects.filter(role='teacher').count()
    total_staff = CustomUser.objects.filter(role__in=['admin', 'non_teaching_staff']).count()
    
    # Get attendance statistics for today
    today = timezone.now().date()
    today_attendance = StudentAttendance.objects.filter(date=today)
    attendance_present = today_attendance.filter(status='present').count()
    attendance_total = today_attendance.count()
    attendance_percentage = (attendance_present / attendance_total * 100) if attendance_total > 0 else 0
    
    # Get class information
    total_classes = ClassGrade.objects.count()
    
    # Get retention alerts
    active_alerts = RetentionAlert.objects.filter(status='open').count()
    
    context = {
        'school': school,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_staff': total_staff,
        'total_classes': total_classes,
        'attendance_present': attendance_present,
        'attendance_total': attendance_total,
        'attendance_percentage': round(attendance_percentage, 1),
        'active_alerts': active_alerts,
    }
    
    return render(request, 'SchoolNowMgt/analytics.html', context)
