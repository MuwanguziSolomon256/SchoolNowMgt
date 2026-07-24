"""
Subject Department Head Dashboard Views
Handles department overview, teacher management, subject management, and performance tracking
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib import messages

from SchoolNowMgt.decorators import require_teacher_role, get_user_school
from SchoolNowMgt.models import (
    CustomUser, StaffProfile, Subject, ClassGrade, Timetable,
    Grade, StudentAttendance, ActivityLog, School, Department,
    TeacherDepartment
)


def paginate_queryset(request, queryset, per_page=15):
    """Helper function to paginate querysets"""
    paginator = Paginator(queryset, per_page)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.page(page_num)
    except PageNotAnInteger:
        page = paginator.page(1)
        page_num = 1
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
        page_num = paginator.num_pages
    return page, paginator, page_num


def get_department_head_department(request, school):
    """Return the department and staff profile for the logged in department head."""
    staff_profile = get_object_or_404(StaffProfile, user=request.user)
    department = TeacherDepartment.objects.filter(
        school=school,
        head_of_department=staff_profile
    ).first()
    return staff_profile, department


@login_required
@require_teacher_role('department_head')
def dept_dashboard(request):
    """Subject Department Head Dashboard - Overview"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subjects = Subject.objects.filter(
        teachers__teacher_department=department,
        teachers__user__school=school
    ).distinct() if department else Subject.objects.none()

    department_teachers = StaffProfile.objects.filter(
        teacher_department=department,
        user__school=school,
        user__role='teacher'
    ).select_related('user') if department else StaffProfile.objects.none()

    classes = ClassGrade.objects.filter(
        school=school,
        timetable_entries__subject__in=subjects
    ).distinct() if department else ClassGrade.objects.none()

    total_subjects = subjects.count()
    total_teachers = department_teachers.count()
    total_classes = classes.count()

    avg_performance = Grade.objects.filter(
        subject__in=subjects,
        student__class_grade__school=school,
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg'] or 0
    avg_performance = round(avg_performance, 1)

    recent_activities = ActivityLog.objects.filter(
        teacher__in=department_teachers,
        activity_type__in=['grade_entered', 'assignment_created', 'lesson_created']
    ).order_by('-created_at')[:5] if department else ActivityLog.objects.none()

    today = timezone.now().date()

    if not department:
        messages.warning(request, 'Your department is not assigned. Please contact the school administrator.')

    context = {
        'today': today,
        'school': school,
        'staff_profile': staff_profile,
        'department': department,
        'subjects': subjects[:8],
        'total_subjects': total_subjects,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'avg_performance': avg_performance,
        'recent_activities': recent_activities,
        'department_teachers': department_teachers,
    }

    return render(request, 'subject_dept/dept_dashboard.html', context)


@login_required
@require_teacher_role('department_head')
def teachers_list(request):
    """List all teachers in department"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    teachers = StaffProfile.objects.filter(
        teacher_department=department,
        user__school=school,
        user__role='teacher'
    ).select_related('user').distinct() if department else StaffProfile.objects.none()

    search_term = request.GET.get('search', '')
    if search_term:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_term) |
            Q(user__last_name__icontains=search_term) |
            Q(employee_id__icontains=search_term)
        )

    status = request.GET.get('status', '')
    if status == 'active':
        teachers = teachers.filter(user__is_active=True)
    elif status == 'inactive':
        teachers = teachers.filter(user__is_active=False)

    page, paginator, page_num = paginate_queryset(request, teachers, per_page=15)

    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'status': status,
        'department': department,
    }

    return render(request, 'subject_dept/teachers_list.html', context)


@login_required
@require_teacher_role('department_head')
def teacher_detail(request, teacher_id):
    """View teacher profile and teaching load"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    teacher = get_object_or_404(
        StaffProfile,
        id=teacher_id,
        user__school=school,
        teacher_department=department
    )

    subjects = Subject.objects.filter(
        teachers=teacher,
        teachers__user__school=school
    ).distinct()

    timetable = Timetable.objects.filter(
        school=school,
        teacher=teacher
    ).select_related('subject', 'class_grade').order_by('day_of_week', 'start_time')

    classes = ClassGrade.objects.filter(
        timetable_entries__teacher=teacher,
        school=school
    ).distinct()

    grades_entered = Grade.objects.filter(
        recorded_by__id=teacher.user.id,
        student__class_grade__school=school
    ).count()

    context = {
        'teacher': teacher,
        'subjects': subjects,
        'classes': classes,
        'timetable': timetable,
        'grades_entered': grades_entered,
        'department': department,
    }

    return render(request, 'subject_dept/teacher_detail.html', context)


@login_required
@require_teacher_role('department_head')
def subjects_list(request):
    """List all subjects in department"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subjects = Subject.objects.filter(
        teachers__teacher_department=department,
        teachers__user__school=school
    ).distinct() if department else Subject.objects.none()

    search_term = request.GET.get('search', '')
    if search_term:
        subjects = subjects.filter(
            Q(name__icontains=search_term) |
            Q(code__icontains=search_term)
        )

    page, paginator, page_num = paginate_queryset(request, subjects, per_page=15)

    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'department': department,
    }

    return render(request, 'subject_dept/subjects_list.html', context)


@login_required
@require_teacher_role('department_head')
def subject_detail(request, subject_id):
    """View subject details and classes"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subject = get_object_or_404(
        Subject,
        id=subject_id,
        teachers__teacher_department=department,
        teachers__user__school=school
    )

    classes = ClassGrade.objects.filter(
        school=school,
        timetable_entries__subject=subject
    ).distinct()

    teachers = StaffProfile.objects.filter(
        user__school=school,
        teacher_department=department,
        subjects=subject
    ).select_related('user').distinct()

    grades = Grade.objects.filter(
        subject=subject,
        student__class_grade__school=school
    ).select_related('student', 'recorded_by')[:10]

    avg_score = Grade.objects.filter(
        subject=subject,
        student__class_grade__school=school,
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg'] or 0
    avg_score = round(avg_score, 1)

    context = {
        'subject': subject,
        'classes': classes,
        'teachers': teachers,
        'grades': grades,
        'avg_score': avg_score,
        'department': department,
    }

    return render(request, 'subject_dept/subject_detail.html', context)


@login_required
@require_teacher_role('department_head')
def classes_list(request):
    """List all classes assigned to department subjects"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subjects = Subject.objects.filter(
        teachers__teacher_department=department,
        teachers__user__school=school
    ).distinct() if department else Subject.objects.none()

    classes = Timetable.objects.filter(
        school=school,
        subject__in=subjects
    ).select_related('class_grade', 'subject', 'teacher').distinct() if department else Timetable.objects.none()

    search_term = request.GET.get('search', '')
    if search_term:
        classes = classes.filter(
            Q(class_grade__name__icontains=search_term) |
            Q(class_grade__level__icontains=search_term)
        )

    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        classes = classes.filter(class_grade__id=grade_filter)

    page, paginator, page_num = paginate_queryset(request, classes, per_page=15)

    all_grades = ClassGrade.objects.filter(school=school).order_by('level', 'name')

    context = {
        'page_obj': page,
        'paginator': paginator,
        'page_num': page_num,
        'search_term': search_term,
        'grade_filter': grade_filter,
        'all_grades': all_grades,
    }

    return render(request, 'subject_dept/classes_list.html', context)


@login_required
@require_teacher_role('department_head')
def timetable_overview(request):
    """View department timetable"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subjects = Subject.objects.filter(
        teachers__teacher_department=department,
        teachers__user__school=school
    ).distinct() if department else Subject.objects.none()

    timetable = Timetable.objects.filter(
        school=school,
        subject__in=subjects
    ).select_related('subject', 'class_grade', 'teacher').order_by('day_of_week', 'start_time') if department else Timetable.objects.none()

    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    timetable_by_day = {day: [] for day in days_order}
    for slot in timetable:
        timetable_by_day.setdefault(slot.day_of_week, []).append(slot)

    context = {
        'timetable_by_day': timetable_by_day,
        'all_timetable': timetable,
    }

    return render(request, 'subject_dept/timetable_overview.html', context)


@login_required
@require_teacher_role('department_head')
def performance_report(request):
    """Department performance metrics"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)

    subjects = Subject.objects.filter(
        teachers__teacher_department=department,
        teachers__user__school=school
    ).distinct() if department else Subject.objects.none()

    subject_performance = []
    for subject in subjects:
        avg_score = Grade.objects.filter(
            subject=subject,
            student__class_grade__school=school,
            score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0

        grades_count = Grade.objects.filter(
            subject=subject,
            student__class_grade__school=school
        ).count()

        subject_performance.append({
            'subject': subject,
            'avg_score': round(avg_score, 1),
            'grades_count': grades_count,
        })

    subject_performance.sort(key=lambda x: x['avg_score'], reverse=True)

    classes = ClassGrade.objects.filter(
        school=school,
        timetable_entries__subject__in=subjects
    ).distinct() if department else ClassGrade.objects.none()

    class_performance = []
    for cls in classes:
        avg_score = Grade.objects.filter(
            student__class_grade=cls,
            student__class_grade__school=school,
            score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0

        class_performance.append({
            'class': cls,
            'avg_score': round(avg_score, 1),
        })

    total_students = StudentAttendance.objects.filter(
        student__class_grade__school=school
    ).values('student').distinct().count()

    department_avg = 0
    if subject_performance:
        department_avg = round(
            sum(item['avg_score'] for item in subject_performance) / len(subject_performance), 1
        )

    context = {
        'subject_performance': subject_performance,
        'class_performance': class_performance,
        'total_students': total_students,
        'department_avg': department_avg,
    }

    return render(request, 'subject_dept/performance_report.html', context)


@login_required
@require_teacher_role('department_head')
def dept_profile(request):
    """View and edit department head profile"""
    school = get_user_school(request)
    staff_profile, department = get_department_head_department(request, school)
    
    if request.method == 'POST':
        # Handle profile update
        user = request.user
        staff = staff_profile
        
        # Update user info
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
        # Update staff profile info
        staff.position = request.POST.get('position', staff.position)
        staff.qualification = request.POST.get('qualification', staff.qualification)
        staff.emergency_contact_name = request.POST.get('emergency_contact_name', staff.emergency_contact_name)
        staff.emergency_contact_phone = request.POST.get('emergency_contact_phone', staff.emergency_contact_phone)
        staff.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('/teacher/department/profile/')
    
    context = {
        'staff_profile': staff_profile,
        'user': request.user,
        'department': department,
        'school': school,
    }
    
    return render(request, 'subject_dept/dept_profile.html', context)
