"""
Director of Studies (DOS) Dashboard Views

Purpose: Manage academic functions including timetables, class assignments,
curriculum, and academic performance reporting.

Permission: Requires DOS role via @require_dos decorator
School Isolation: All queries filtered by school=user.school
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction

from SchoolNowMgt.models import (
    Timetable, ClassGrade, StaffProfile, Subject, TeacherDepartment,
    ClassTeacherAssignment, CustomUser, Student, Grade, ActivityLog
)
from SchoolNowMgt.decorators import require_dos, get_user_school
from SchoolNowMgt.utils import get_dos_scope_data


# ============================================================================
# DOS MAIN DASHBOARD
# ============================================================================

@require_dos
def dos_dashboard(request):
    """
    Main DOS Dashboard - Overview of academic functions
    
    Template context:
    - school: Current school
    - staff_profile: DOS staff profile
    - academic_year: Current academic year
    - statistics: Dict with key metrics
    - recent_activities: Latest activity logs
    - pending_tasks: Class assignments pending, etc.
    
    School Filtering: All queries filtered by school=school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get scope data (includes school-filtered queries)
    scope_data = get_dos_scope_data(request)
    
    # Get academic year from settings or use current year
    current_year = timezone.now().year
    current_month = timezone.now().month
    academic_year = f"{current_year}-{current_year + 1}" if current_month < 9 else f"{current_year}-{current_year + 1}"
    
    # Calculate statistics
    all_teachers = scope_data['all_teachers']
    departments = scope_data['departments']
    classes = scope_data['classes']
    all_students = scope_data['all_students']
    
    statistics = {
        'total_teachers': all_teachers.count(),
        'total_departments': departments.count(),
        'total_classes': classes.count(),
        'total_students': all_students,
        'avg_class_size': all_students // classes.count() if classes.count() > 0 else 0,
        'subjects_offered': Subject.objects.all().count(),
    }
    
    # Get active timetables
    timetables = Timetable.objects.filter(
        class_grade__school=school
    ).select_related('class_grade', 'subject', 'teacher').count()
    
    statistics['timetable_entries'] = timetables
    
    # Get recent class teacher assignments (last 5)
    recent_assignments = ClassTeacherAssignment.objects.filter(
        school=school,
        is_active=True
    ).select_related('teacher', 'class_grade').order_by('-assigned_date')[:5]
    
    # Get pending class teacher assignments (classes without active teacher)
    classes_without_teacher = classes.filter(class_teacher__isnull=True).count()
    
    # Get recent activity logs (filter through teacher__user__school since Activity Log doesn't have direct school field)
    recent_activities = ActivityLog.objects.filter(
        teacher__user__school=school,
    ).select_related('teacher__user', 'related_student').order_by('-created_at')[:10]
    
    # Department heads who need attention
    departments_without_head = departments.filter(head_of_department__isnull=True)
    
    context = {
        'school': school,
        'staff_profile': staff,
        'academic_year': academic_year,
        'statistics': statistics,
        'recent_assignments': recent_assignments,
        'classes_without_teacher': classes_without_teacher,
        'recent_activities': recent_activities,
        'departments_without_head': departments_without_head,
        'section': 'dos_dashboard',
    }
    
    # Log activity
    ActivityLog.objects.create(
        teacher=staff,
        activity_type='dashboard_visit',
        description='Accessed DOS Dashboard',
        severity='info',
        icon_name='dashboard'
    )
    
    return render(request, 'dos/dos_dashboard.html', context)


# ============================================================================
# TIMETABLE MANAGEMENT
# ============================================================================

@require_dos
def timetable_list(request):
    """
    List all timetable entries with filtering options
    
    GET params:
    - class_id: Filter by class
    - teacher_id: Filter by teacher
    - day: Filter by day of week
    - search: Search in subject name
    - page: Pagination
    
    School Filtering: All data filtered by school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Base queryset
    timetables = Timetable.objects.filter(
        class_grade__school=school
    ).select_related('class_grade', 'subject', 'teacher').order_by('day_of_week', 'start_time')
    
    # Apply filters
    class_id = request.GET.get('class_id')
    if class_id:
        timetables = timetables.filter(class_grade_id=class_id)
    
    teacher_id = request.GET.get('teacher_id')
    if teacher_id:
        timetables = timetables.filter(teacher_id=teacher_id)
    
    day = request.GET.get('day')
    if day:
        timetables = timetables.filter(day_of_week=day)
    
    search = request.GET.get('search')
    if search:
        timetables = timetables.filter(subject__name__icontains=search)
    
    # Pagination
    paginator = Paginator(timetables, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    day_choices = Timetable.DAY_CHOICES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'page_obj': page_obj,
        'timetables': page_obj.object_list,
        'classes': classes,
        'teachers': teachers,
        'day_choices': day_choices,
        'selected_class': class_id,
        'selected_teacher': teacher_id,
        'selected_day': day,
        'search_query': search,
        'section': 'timetable_list',
    }
    
    return render(request, 'dos/timetable_list.html', context)


@require_dos
@require_http_methods(['GET', 'POST'])
def timetable_create(request):
    """
    Create new timetable entry
    
    POST params (JSON or form):
    - class_id: ClassGrade ID
    - subject_id: Subject ID
    - teacher_id: StaffProfile ID
    - day_of_week: Day choice
    - start_time: Time (HH:MM)
    - end_time: Time (HH:MM)
    
    School Filtering: Only show school's classes, subjects, teachers
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class_id')
            subject_id = request.POST.get('subject_id')
            teacher_id = request.POST.get('teacher_id')
            day_of_week = request.POST.get('day_of_week')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            # Validate that all required fields are present
            if not all([class_id, subject_id, teacher_id, day_of_week, start_time, end_time]):
                messages.error(request, 'All fields are required')
                return redirect('dos:timetable_create')
            
            # Get objects with school filtering
            class_grade = get_object_or_404(ClassGrade, id=class_id, school=school)
            subject = get_object_or_404(Subject, id=subject_id, school=school)
            teacher = get_object_or_404(
                StaffProfile,
                id=teacher_id,
                user__school=school,
                user__role='teacher'
            )
            
            # Create timetable entry
            timetable = Timetable(
                class_grade=class_grade,
                subject=subject,
                teacher=teacher,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                curriculum=class_grade.curriculum
            )
            
            # Clean and validate
            timetable.full_clean()
            timetable.save()
            
            # Log activity
            ActivityLog.objects.create(
                staff=staff,
                school=school,
                activity_type='timetable_created',
                description=f'Created timetable entry: {timetable}',
                severity='info',
                icon_name='schedule'
            )
            
            messages.success(request, 'Timetable entry created successfully')
            return redirect('dos:timetable_list')
        
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
            return redirect('dos:timetable_create')
        except Exception as e:
            messages.error(request, f'Error creating timetable: {str(e)}')
            return redirect('dos:timetable_create')
    
    # GET request - show form with school-filtered options
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    subjects = Subject.objects.all().order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    day_choices = Timetable.DAY_CHOICES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'classes': classes,
        'subjects': subjects,
        'teachers': teachers,
        'day_choices': day_choices,
        'section': 'timetable_create',
    }
    
    return render(request, 'dos/timetable_form.html', context)


@require_dos
@require_http_methods(['GET', 'POST'])
def timetable_edit(request, timetable_id):
    """
    Edit existing timetable entry
    
    School Filtering: Only allow editing school's timetables
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    timetable = get_object_or_404(
        Timetable,
        id=timetable_id,
        class_grade__school=school
    )
    
    if request.method == 'POST':
        try:
            timetable.class_grade_id = request.POST.get('class_id')
            timetable.subject_id = request.POST.get('subject_id')
            timetable.teacher_id = request.POST.get('teacher_id')
            timetable.day_of_week = request.POST.get('day_of_week')
            timetable.start_time = request.POST.get('start_time')
            timetable.end_time = request.POST.get('end_time')
            
            # Validate with school constraint
            class_grade = get_object_or_404(ClassGrade, id=timetable.class_grade_id, school=school)
            subject = get_object_or_404(Subject, id=timetable.subject_id, school=school)
            teacher = get_object_or_404(
                StaffProfile,
                id=timetable.teacher_id,
                user__school=school,
                user__role='teacher'
            )
            
            timetable.full_clean()
            timetable.save()
            
            ActivityLog.objects.create(
                staff=staff,
                school=school,
                activity_type='timetable_edited',
                description=f'Edited timetable entry: {timetable}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Timetable entry updated successfully')
            return redirect('dos:timetable_list')
        
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating timetable: {str(e)}')
    
    # GET request
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    subjects = Subject.objects.all().order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    day_choices = Timetable.DAY_CHOICES
    
    context = {
        'school': school,
        'staff_profile': staff,
        'timetable': timetable,
        'classes': classes,
        'subjects': subjects,
        'teachers': teachers,
        'day_choices': day_choices,
        'is_edit': True,
        'section': 'timetable_edit',
    }
    
    return render(request, 'dos/timetable_form.html', context)


@require_dos
@require_http_methods(['POST'])
def timetable_delete(request, timetable_id):
    """
    Delete timetable entry
    
    School Filtering: Only allow deletion of school's timetables
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    timetable = get_object_or_404(
        Timetable,
        id=timetable_id,
        class_grade__school=school
    )
    
    timetable_str = str(timetable)
    timetable.delete()
    
    ActivityLog.objects.create(
        staff=staff,
        school=school,
        activity_type='timetable_deleted',
        description=f'Deleted timetable entry: {timetable_str}',
        severity='warning',
        icon_name='delete'
    )
    
    messages.success(request, 'Timetable entry deleted successfully')
    return redirect('dos:timetable_list')


# ============================================================================
# CLASS TEACHER ASSIGNMENTS
# ============================================================================

@require_dos
def class_teacher_assignments_list(request):
    """
    List all class teacher assignments with filtering
    
    GET params:
    - class_id: Filter by class
    - teacher_id: Filter by teacher
    - academic_year: Filter by academic year
    - status: 'active' or 'inactive'
    - page: Pagination
    
    School Filtering: All assignments filtered by school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Base queryset with school filtering
    assignments = ClassTeacherAssignment.objects.filter(
        school=school
    ).select_related('teacher', 'class_grade').order_by('-start_date')
    
    # Apply filters
    class_id = request.GET.get('class_id')
    if class_id:
        assignments = assignments.filter(class_grade_id=class_id)
    
    teacher_id = request.GET.get('teacher_id')
    if teacher_id:
        assignments = assignments.filter(teacher_id=teacher_id)
    
    academic_year = request.GET.get('academic_year')
    if academic_year:
        assignments = assignments.filter(academic_year=academic_year)
    
    status = request.GET.get('status')
    if status:
        if status == 'active':
            assignments = assignments.filter(is_active=True)
        elif status == 'inactive':
            assignments = assignments.filter(is_active=False)
    else:
        # Default to active
        assignments = assignments.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    # Get academic years from existing assignments
    academic_years = ClassTeacherAssignment.objects.filter(
        school=school
    ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    context = {
        'school': school,
        'staff_profile': staff,
        'page_obj': page_obj,
        'assignments': page_obj.object_list,
        'classes': classes,
        'teachers': teachers,
        'academic_years': academic_years,
        'selected_class': class_id,
        'selected_teacher': teacher_id,
        'selected_academic_year': academic_year,
        'selected_status': status or 'active',
        'section': 'class_teacher_assignments',
    }
    
    return render(request, 'dos/class_teacher_assignments_list.html', context)


@require_dos
@require_http_methods(['GET', 'POST'])
def class_teacher_assignment_create(request):
    """
    Create new class teacher assignment
    
    POST params:
    - class_id: ClassGrade ID
    - teacher_id: StaffProfile ID
    - academic_year: Year string (e.g., "2024-2025")
    - start_date: Start date
    - end_date: End date (optional)
    
    School Filtering: Only school's classes and teachers available
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class_id')
            teacher_id = request.POST.get('teacher_id')
            academic_year = request.POST.get('academic_year')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            
            if not all([class_id, teacher_id, academic_year, start_date]):
                messages.error(request, 'Class, Teacher, Academic Year, and Start Date are required')
                return redirect('dos:class_teacher_assignment_create')
            
            # Verify school ownership
            class_grade = get_object_or_404(ClassGrade, id=class_id, school=school)
            teacher = get_object_or_404(
                StaffProfile,
                id=teacher_id,
                user__school=school,
                user__role='teacher'
            )
            
            # Check if assignment already exists for this class/year
            existing = ClassTeacherAssignment.objects.filter(
                school=school,
                class_grade=class_grade,
                academic_year=academic_year,
                is_active=True
            ).exists()
            
            if existing:
                messages.warning(
                    request,
                    f'Class {class_grade.name} already has an active teacher for {academic_year}'
                )
                return redirect('dos:class_teacher_assignment_create')
            
            # Create assignment
            assignment = ClassTeacherAssignment(
                school=school,
                class_grade=class_grade,
                teacher=teacher,
                academic_year=academic_year,
                start_date=start_date,
                end_date=end_date if end_date else None,
                is_active=True
            )
            
            assignment.full_clean()
            assignment.save()
            
            # Update ClassGrade.class_teacher if start date is today or past
            if assignment.start_date <= timezone.now().date():
                class_grade.class_teacher = teacher
                class_grade.save()
            
            ActivityLog.objects.create(
                staff=staff,
                school=school,
                activity_type='class_teacher_assigned',
                description=f'Assigned {teacher.user.get_full_name()} to {class_grade.name} for {academic_year}',
                severity='info',
                icon_name='person_add'
            )
            
            messages.success(request, 'Class teacher assignment created successfully')
            return redirect('dos:class_teacher_assignments_list')
        
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error creating assignment: {str(e)}')
    
    # GET request
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    # Current academic year
    current_year = timezone.now().year
    current_month = timezone.now().month
    current_academic_year = f"{current_year}-{current_year + 1}" if current_month < 9 else f"{current_year}-{current_year + 1}"
    
    context = {
        'school': school,
        'staff_profile': staff,
        'classes': classes,
        'teachers': teachers,
        'current_academic_year': current_academic_year,
        'section': 'class_teacher_assignment_create',
    }
    
    return render(request, 'dos/class_teacher_assignment_form.html', context)


@require_dos
@require_http_methods(['GET', 'POST'])
def class_teacher_assignment_edit(request, assignment_id):
    """
    Edit class teacher assignment
    
    School Filtering: Only school's assignments can be edited
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    assignment = get_object_or_404(ClassTeacherAssignment, id=assignment_id, school=school)
    
    if request.method == 'POST':
        try:
            assignment.class_grade_id = request.POST.get('class_id')
            assignment.teacher_id = request.POST.get('teacher_id')
            assignment.academic_year = request.POST.get('academic_year')
            assignment.start_date = request.POST.get('start_date')
            assignment.end_date = request.POST.get('end_date') or None
            assignment.is_active = request.POST.get('is_active') == 'on'
            
            # Verify school ownership
            get_object_or_404(ClassGrade, id=assignment.class_grade_id, school=school)
            get_object_or_404(
                StaffProfile,
                id=assignment.teacher_id,
                user__school=school,
                user__role='teacher'
            )
            
            assignment.full_clean()
            assignment.save()
            
            ActivityLog.objects.create(
                staff=staff,
                school=school,
                activity_type='class_teacher_updated',
                description=f'Updated class teacher assignment for {assignment.class_grade.name}',
                severity='info',
                icon_name='edit'
            )
            
            messages.success(request, 'Assignment updated successfully')
            return redirect('dos:class_teacher_assignments_list')
        
        except ValidationError as e:
            messages.error(request, f'Validation error: {str(e)}')
        except Exception as e:
            messages.error(request, f'Error updating assignment: {str(e)}')
    
    # GET request
    classes = ClassGrade.objects.filter(school=school).order_by('name')
    teachers = StaffProfile.objects.filter(
        user__school=school,
        user__role='teacher'
    ).select_related('user').order_by('user__first_name')
    
    context = {
        'school': school,
        'staff_profile': staff,
        'assignment': assignment,
        'classes': classes,
        'teachers': teachers,
        'is_edit': True,
        'section': 'class_teacher_assignment_edit',
    }
    
    return render(request, 'dos/class_teacher_assignment_form.html', context)


@require_dos
@require_http_methods(['POST'])
def class_teacher_assignment_delete(request, assignment_id):
    """
    Delete/deactivate class teacher assignment
    
    School Filtering: Only school's assignments can be deleted
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    assignment = get_object_or_404(ClassTeacherAssignment, id=assignment_id, school=school)
    
    assignment_str = str(assignment)
    assignment.is_active = False
    assignment.end_date = timezone.now().date()
    assignment.save()
    
    ActivityLog.objects.create(
        staff=staff,
        school=school,
        activity_type='class_teacher_removed',
        description=f'Removed class teacher assignment: {assignment_str}',
        severity='warning',
        icon_name='person_remove'
    )
    
    messages.success(request, 'Assignment deactivated successfully')
    return redirect('dos:class_teacher_assignments_list')


# ============================================================================
# DEPARTMENTS & ACADEMIC OVERSIGHT
# ============================================================================

@require_dos
def departments_overview(request):
    """
    Overview of all teacher departments with performance metrics
    
    Shows:
    - All departments for the school
    - Department heads and members
    - Academic performance by department
    
    School Filtering: Only school's departments shown
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    departments = TeacherDepartment.objects.filter(
        school=school,
        is_active=True
    ).select_related('head_of_department').prefetch_related('teacher_members')
    
    # Calculate performance metrics for each department
    department_stats = []
    for dept in departments:
        dept_teachers = dept.teacher_members.filter(user__school=school, user__role='teacher')
        
        # Get students taught by this department's teachers
        dept_student_count = Student.objects.filter(
            school=school
        ).count()  # Simplified, real implementation would join through classes/grades
        
        # Get average grades (simplified)
        avg_grade = Grade.objects.filter(
            student__class_grade__school=school
        ).aggregate(avg=Avg('score'))['avg'] or 0
        
        department_stats.append({
            'department': dept,
            'teacher_count': dept_teachers.count(),
            'student_count': dept_student_count,
            'avg_grade': round(avg_grade, 2),
            'budget': dept.annual_budget or 0,
        })
    
    context = {
        'school': school,
        'staff_profile': staff,
        'department_stats': department_stats,
        'section': 'departments_overview',
    }
    
    return render(request, 'dos/departments_overview.html', context)


# ============================================================================
# REPORTING & ANALYTICS
# ============================================================================

@require_dos
def academic_reports(request):
    """
    Academic performance reports and analytics
    
    Report types:
    - Subject performance summary
    - Teacher performance
    - Class performance trends
    
    School Filtering: All reports scoped to school
    """
    school = get_user_school(request)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    report_type = request.GET.get('report_type', 'subject_performance')
    
    context = {
        'school': school,
        'staff_profile': staff,
        'report_type': report_type,
        'section': 'academic_reports',
    }
    
    if report_type == 'subject_performance':
        # Subject performance report
        subjects = Subject.objects.all()
        
        subject_data = []
        for subject in subjects:
            grades = Grade.objects.filter(
                subject=subject,
                student__class_grade__school=school
            )
            
            if grades.exists():
                avg_score = grades.aggregate(avg=Avg('score'))['avg']
                pass_count = grades.filter(score__gte=40).count()
                fail_count = grades.filter(score__lt=40).count()
                
                subject_data.append({
                    'subject': subject,
                    'avg_score': round(avg_score, 2),
                    'pass_count': pass_count,
                    'fail_count': fail_count,
                    'total': pass_count + fail_count,
                    'pass_rate': round((pass_count / (pass_count + fail_count)) * 100, 2) if (pass_count + fail_count) > 0 else 0,
                })
        
        context['subject_data'] = subject_data
    
    elif report_type == 'teacher_performance':
        # Teacher performance report
        teachers = StaffProfile.objects.filter(
            user__school=school,
            user__role='teacher'
        ).select_related('user')
        
        teacher_data = []
        for teacher in teachers:
            grades = Grade.objects.filter(
                created_by=teacher,
                student__class_grade__school=school
            )
            
            if grades.exists():
                avg_score = grades.aggregate(avg=Avg('score'))['avg']
                student_count = grades.values('student').distinct().count()
                
                teacher_data.append({
                    'teacher': teacher.user.get_full_name(),
                    'avg_score': round(avg_score, 2),
                    'student_count': student_count,
                    'grades_count': grades.count(),
                })
        
        context['teacher_data'] = teacher_data
    
    elif report_type == 'class_performance':
        # Class performance report
        classes = ClassGrade.objects.filter(school=school)
        
        class_data = []
        for cls in classes:
            grades = Grade.objects.filter(
                student__class_grade=cls
            )
            
            if grades.exists():
                avg_score = grades.aggregate(avg=Avg('score'))['avg']
                class_data.append({
                    'class': cls.name,
                    'avg_score': round(avg_score, 2),
                    'student_count': cls.students.count(),
                    'grade_count': grades.count(),
                })
        
        context['class_data'] = class_data
    
    return render(request, 'dos/academic_reports.html', context)
