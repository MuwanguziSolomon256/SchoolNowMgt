"""
Teacher Sub-Dashboards Views

Provides views for:
1. Grades - View, enter, export, and analyze student grades
2. Communication - Messaging system for teacher-to-parent/colleague/admin communication
3. Attendances - Mark and track student attendance with offline-first support
4. Gradebook - Reference chart for Uganda national grading standards
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg, F, Case, When, IntegerField, Max, Min
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
import json
import csv
from io import BytesIO
from datetime import timedelta, datetime
from decimal import Decimal

from SchoolNowMgt.models import (
    Grade, Subject, ClassGrade, Student, StudentAttendance,
    Message, MessageRecipient, MessageTemplate, CustomUser,
    TeacherTask, ActivityLog, StaffProfile
)
from curriculum.uganda_constants import UGANDA_TERMS
from SchoolNowMgt.utils import (
    resolve_message_recipients, create_message_recipients,
    replace_message_placeholders
)


# ========================
# UTILITY DECORATORS & HELPERS
# ========================

def teacher_required(view_func):
    """Decorator to ensure only teachers can access the view."""
    def wrapped_view(request, *args, **kwargs):
        if request.user.role != 'teacher':
            return redirect('teacher:login')
        return view_func(request, *args, **kwargs)
    return login_required(login_url='teacher:login')(wrapped_view)


def get_teacher_staff_profile(request):
    """Get the StaffProfile for the logged-in teacher or return None."""
    try:
        return StaffProfile.objects.get(user=request.user)
    except StaffProfile.DoesNotExist:
        return None


def get_teacher_classes(staff_profile):
    """Get all active classes where the staff is class_teacher."""
    if not staff_profile:
        return ClassGrade.objects.none()
    return ClassGrade.objects.filter(
        class_teacher=staff_profile
    ).select_related('school').prefetch_related('students')


# ========================
# GRADES SUB-DASHBOARD
# ========================

@teacher_required
def grades_dashboard(request):
    """
    Main grades dashboard - view grades by class and subject.
    
    Context:
    - classes: List of teacher's classes with student counts
    - selected_class: Currently selected class (from GET param)
    - grades_table: Grades data for selected class organized by subject
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    # Get all teacher's classes
    classes = get_teacher_classes(staff)
    
    # Get selected class (default to first one)
    class_id = request.GET.get('class_id')
    if class_id:
        selected_class = get_object_or_404(classes, id=class_id)
    else:
        selected_class = classes.first()
    
    # Build grades table
    grades_by_subject = {}
    if selected_class:
        # Get all subjects taught in this class
        subjects = Subject.objects.all().order_by('name')
        
        # Get current term/year
        today = timezone.localdate()
        current_term = 1  # TODO: Get from settings or calculate
        current_year = today.year
        
        # Fetch all grades for this class
        grades_qs = Grade.objects.filter(
            student__class_grade=selected_class,
            term=current_term,
            academic_year=current_year
        ).select_related('student', 'subject')
        
        # Organize by subject
        for subject in subjects:
            grades_by_subject[subject] = grades_qs.filter(subject=subject)
    
    nav_items = [
        {'label': 'List', 'url': reverse('teacher:grades_dashboard'), 'icon': 'assessment', 'is_active': request.path == '/teacher/grades/'},
        {'label': 'Entry', 'url': reverse('teacher:grade_entry'), 'icon': 'edit', 'is_active': request.path == '/teacher/grades/entry/'},
        {'label': 'Statistics', 'url': reverse('teacher:grade_statistics'), 'icon': 'bar_chart', 'is_active': request.path == '/teacher/grades/statistics/'},
        {'label': 'Export', 'url': reverse('teacher:grade_export'), 'icon': 'download', 'is_active': request.path == '/teacher/grades/export/'},
        {'label': 'History', 'url': reverse('teacher:grade_history'), 'icon': 'history', 'is_active': request.path == '/teacher/grades/history/'},
    ]
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'grades_by_subject': grades_by_subject,
        'today': timezone.localdate(),
        'breadcrumb_title': 'Grades - View & Analyze',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/grades/grades_list.html', context)


@teacher_required
def grade_entry_interface(request):
    """
    Bulk grade entry interface - spreadsheet-like entry for a class/subject.
    
    GET: Show form to select class and subject
    POST (AJAX): Save grades and return success/error
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    # Get subjects taught by this teacher
    subjects = Subject.objects.filter(
        timetable_entries__teacher=staff
    ).distinct().order_by('name')
    
    if request.method == 'GET':
        nav_items = [
            {'label': 'List', 'url': reverse('teacher:grades_dashboard'), 'icon': 'assessment', 'is_active': request.path == '/teacher/grades/'},
            {'label': 'Entry', 'url': reverse('teacher:grade_entry'), 'icon': 'edit', 'is_active': request.path == '/teacher/grades/entry/'},
            {'label': 'Statistics', 'url': reverse('teacher:grade_statistics'), 'icon': 'bar_chart', 'is_active': request.path == '/teacher/grades/statistics/'},
            {'label': 'Export', 'url': reverse('teacher:grade_export'), 'icon': 'download', 'is_active': request.path == '/teacher/grades/export/'},
            {'label': 'History', 'url': reverse('teacher:grade_history'), 'icon': 'history', 'is_active': request.path == '/teacher/grades/history/'},
        ]
        
        # Get all students for single entry dropdown
        all_students = Student.objects.select_related('class_grade').filter(
            status='active'
        ).order_by('first_name', 'last_name')
        
        context = {
            'classes': classes,
            'subjects': subjects,
            'all_students': all_students,
            'terms': [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')],
            'current_term': '1',
            'current_year': timezone.now().year,
            'breadcrumb_title': 'Grades - Entry Interface',
            'nav_items': nav_items,
        }
        return render(request, 'teacher/sub_dashboards/grades/grade_entry.html', context)
    
    elif request.method == 'POST':
        # Handle AJAX grade entry submission (both bulk and single)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        
        # Determine entry type (bulk or single)
        entry_type = data.get('entry_type', 'bulk')
        
        if entry_type == 'single':
            # ===== SINGLE ENTRY HANDLER =====
            student_id = data.get('student_id')
            subject_id = data.get('subject_id')
            term = data.get('term', '1')
            year = data.get('year', str(timezone.now().year))
            score = data.get('score')
            
            # Validation
            if not student_id or not subject_id or score is None:
                return JsonResponse({
                    'success': False,
                    'error': 'Student, subject, and score are required'
                }, status=400)
            
            try:
                score = float(score)
                if not 0 <= score <= 100:
                    return JsonResponse({
                        'success': False,
                        'error': 'Score must be between 0 and 100'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid score format'
                }, status=400)
            
            try:
                student = Student.objects.get(id=student_id)
                subject_obj = Subject.objects.get(id=subject_id)
            except (Student.DoesNotExist, Subject.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid student or subject'
                }, status=404)
            
            # Create or update grade
            grade_term = f'term_{term}' if term.isdigit() else term
            grade, created = Grade.objects.update_or_create(
                student=student,
                subject=subject_obj,
                curriculum='national',
                term=grade_term,
                semester='',
                academic_year=str(year),
                defaults={
                    'score': Decimal(str(score)),
                    'recorded_by': request.user,
                }
            )
            
            # Log activity
            ActivityLog.objects.create(
                teacher=staff,
                activity_type='grade_entered',
                description=f'Entered grade for {student.first_name} {student.last_name} in {subject_obj.name}: {score}',
                severity='success',
                icon_name='assignment'
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'student_name': f'{student.first_name} {student.last_name}',
                    'subject': subject_obj.name,
                    'score': score,
                    'grade': grade.id,
                    'created': created,
                }
            })
        
        else:
            # ===== BULK ENTRY HANDLER =====
            class_id = data.get('class_id')
            subject_id = data.get('subject_id')
            term = data.get('term', '1')
            year = data.get('year', str(timezone.now().year))
            grades_data = data.get('grades', {})  # {student_id: score, ...}
            
            # Validation
            if not class_id or not subject_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Class and subject are required'
                }, status=400)
            
            try:
                class_obj = ClassGrade.objects.get(id=class_id, school=request.user.school)
                subject_obj = Subject.objects.get(id=subject_id)
            except (ClassGrade.DoesNotExist, Subject.DoesNotExist):
                return JsonResponse({'success': False, 'error': 'Invalid class or subject'}, status=404)
            
            # Process grades
            created_count = 0
            updated_count = 0
            failed_entries = []
            
            for student_id_str, score_str in grades_data.items():
                try:
                    student_id = int(student_id_str)
                    score = float(score_str)
                    
                    # Validate score
                    if not 0 <= score <= 100:
                        failed_entries.append(f"Student {student_id}: Score out of range (0-100)")
                        continue
                    
                    student = Student.objects.get(
                        id=student_id,
                        class_grade=class_obj,
                        status='active'
                    )
                    
                    # Create or update grade
                    grade_term = f'term_{term}' if term.isdigit() else term
                    grade, created = Grade.objects.update_or_create(
                        student=student,
                        subject=subject_obj,
                        curriculum='national',
                        term=grade_term,
                        semester='',
                        academic_year=str(year),
                        defaults={
                            'score': Decimal(str(score)),
                            'recorded_by': request.user,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                
                except (ValueError, Student.DoesNotExist) as e:
                    failed_entries.append(f"Student {student_id_str}: {str(e)}")
                    continue
            
            # Log activity
            ActivityLog.objects.create(
                teacher=staff,
                activity_type='grade_entered',
                description=f'Entered {class_obj.name} {subject_obj.name} grades: {created_count} new, {updated_count} updated',
                severity='success',
                icon_name='assignment'
            )
            
            return JsonResponse({
                'success': True,
                'data': {
                    'created_count': created_count,
                    'updated_count': updated_count,
                    'total_saved': created_count + updated_count,
                    'failed_count': len(failed_entries),
                    'failed_entries': failed_entries,
                }
            })


@teacher_required
def grade_statistics(request):
    """
    Grade statistics and analytics - averages, distributions, trends.
    
    Context:
    - class_stats: Per-class statistics (average, distribution)
    - subject_stats: Per-subject statistics
    - student_distribution: Chart data for grade distribution
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    # Get selected class (for detailed view)
    class_id = request.GET.get('class_id')
    selected_class = None
    class_stats = None
    subject_stats = None
    grade_distribution = None
    
    if class_id:
        try:
            selected_class = classes.get(id=class_id)
        except ClassGrade.DoesNotExist:
            selected_class = None
    
    if selected_class:
        # Get current term/year
        today = timezone.localdate()
        current_year = today.year
        current_term = 'term_1'  # Default, could be calculated from settings
        
        # Get all grades for this class
        grades_qs = Grade.objects.filter(
            student__class_grade=selected_class,
            term=current_term,
            academic_year=current_year
        ).select_related('student', 'subject')
        
        if grades_qs.exists():
            # Overall class statistics
            avg_score = grades_qs.aggregate(avg=Avg('score'))['avg']
            max_score = grades_qs.aggregate(max=Max('score'))['max']
            min_score = grades_qs.aggregate(min=Min('score'))['min']
            
            class_stats = {
                'average': round(avg_score, 2) if avg_score else 0,
                'highest': round(max_score, 2) if max_score else 0,
                'lowest': round(min_score, 2) if min_score else 0,
                'total_records': grades_qs.count(),
            }
            
            # Grade distribution (A, B, C, D, E counts)
            grade_counts = {
                'A': grades_qs.filter(score__gte=75).count(),
                'B': grades_qs.filter(score__gte=65, score__lt=75).count(),
                'C': grades_qs.filter(score__gte=50, score__lt=65).count(),
                'D': grades_qs.filter(score__gte=40, score__lt=50).count(),
                'E': grades_qs.filter(score__lt=40).count(),
            }
            
            grade_distribution = {
                'labels': ['A', 'B', 'C', 'D', 'E'],
                'data': [grade_counts['A'], grade_counts['B'], grade_counts['C'], grade_counts['D'], grade_counts['E']],
                'colors': ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'],
            }
            
            # Per-subject statistics
            subject_stats_list = []
            for subject in Subject.objects.all().distinct():
                subject_grades = grades_qs.filter(subject=subject)
                if subject_grades.exists():
                    subject_avg = subject_grades.aggregate(avg=Avg('score'))['avg']
                    subject_stats_list.append({
                        'name': subject.name,
                        'average': round(subject_avg, 2),
                        'count': subject_grades.count(),
                    })
            
            subject_stats = sorted(subject_stats_list, key=lambda x: x['average'], reverse=True)
    
    nav_items = [
        {'label': 'List', 'url': reverse('teacher:grades_dashboard'), 'icon': 'assessment', 'is_active': request.path == '/teacher/grades/'},
        {'label': 'Entry', 'url': reverse('teacher:grade_entry'), 'icon': 'edit', 'is_active': request.path == '/teacher/grades/entry/'},
        {'label': 'Statistics', 'url': reverse('teacher:grade_statistics'), 'icon': 'bar_chart', 'is_active': request.path == '/teacher/grades/statistics/'},
        {'label': 'Export', 'url': reverse('teacher:grade_export'), 'icon': 'download', 'is_active': request.path == '/teacher/grades/export/'},
        {'label': 'History', 'url': reverse('teacher:grade_history'), 'icon': 'history', 'is_active': request.path == '/teacher/grades/history/'},
    ]
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'class_stats': class_stats,
        'subject_stats': subject_stats,
        'grade_distribution': grade_distribution,
        'breadcrumb_title': 'Grades - Statistics & Analysis',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/grades/grade_statistics.html', context)


@teacher_required
def grade_export(request):
    """
    Export grades to CSV or PDF format.
    
    GET params:
    - format: 'csv' or 'pdf'
    - class_id: Filter by class
    - term: Filter by term
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    if request.method == 'GET':
        # Show export options form
        nav_items = [
            {'label': 'List', 'url': reverse('teacher:grades_dashboard'), 'icon': 'assessment', 'is_active': request.path == '/teacher/grades/'},
            {'label': 'Entry', 'url': reverse('teacher:grade_entry'), 'icon': 'edit', 'is_active': request.path == '/teacher/grades/entry/'},
            {'label': 'Statistics', 'url': reverse('teacher:grade_statistics'), 'icon': 'bar_chart', 'is_active': request.path == '/teacher/grades/statistics/'},
            {'label': 'Export', 'url': reverse('teacher:grade_export'), 'icon': 'download', 'is_active': request.path == '/teacher/grades/export/'},
            {'label': 'History', 'url': reverse('teacher:grade_history'), 'icon': 'history', 'is_active': request.path == '/teacher/grades/history/'},
        ]
        
        context = {
            'classes': classes,
            'terms': UGANDA_TERMS,
            'breadcrumb_title': 'Grades - Export Data',
            'nav_items': nav_items,
        }
        return render(request, 'teacher/sub_dashboards/grades/grade_export_form.html', context)
    
    elif request.method == 'POST':
        # Handle export request (AJAX)
        export_format = request.POST.get('format', 'csv')
        class_id = request.POST.get('class_id')
        term = request.POST.get('term', '1')
        year = request.POST.get('year', timezone.now().year)
        
        if export_format == 'csv':
            return export_grades_csv(staff, class_id, term, year, request.user.school)
        else:
            return JsonResponse({'error': 'PDF export not yet implemented'}, status=501)


def export_grades_csv(staff, class_id, term, year, school):
    """Generate CSV export of grades."""
    # Get selected class
    class_obj = ClassGrade.objects.get(id=class_id, school=school)
    
    # Fetch grades
    grades = Grade.objects.filter(
        student__class_grade=class_obj,
        student__school=school,
        term=term,
        academic_year=year
    ).select_related('student', 'subject').order_by('student__first_name', 'subject__name')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="grades_{class_obj.name}_{year}_t{term}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Student ID', 'Name', 'Subject', 'Score', 'Grade', 'Remarks'])
    
    for grade in grades:
        writer.writerow([
            grade.student.id,
            grade.student.get_full_name(),
            grade.subject.name,
            grade.score,
            grade.get_grade_display(),
            grade.remarks or ''
        ])
    
    return response


@teacher_required
def grade_history(request):
    """
    Student grade history - term-to-term progression.
    
    GET params:
    - student_id: Filter by specific student
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    # Get selected student
    student_id = request.GET.get('student_id')
    selected_student = None
    if student_id:
        # Get student from teacher's classes
        selected_student = get_object_or_404(
            Student.objects.filter(class_grade__in=classes),
            id=student_id
        )
    
    nav_items = [
        {'label': 'List', 'url': reverse('teacher:grades_dashboard'), 'icon': 'assessment', 'is_active': request.path == '/teacher/grades/'},
        {'label': 'Entry', 'url': reverse('teacher:grade_entry'), 'icon': 'edit', 'is_active': request.path == '/teacher/grades/entry/'},
        {'label': 'Statistics', 'url': reverse('teacher:grade_statistics'), 'icon': 'bar_chart', 'is_active': request.path == '/teacher/grades/statistics/'},
        {'label': 'Export', 'url': reverse('teacher:grade_export'), 'icon': 'download', 'is_active': request.path == '/teacher/grades/export/'},
        {'label': 'History', 'url': reverse('teacher:grade_history'), 'icon': 'history', 'is_active': request.path == '/teacher/grades/history/'},
    ]
    
    context = {
        'classes': classes,
        'selected_student': selected_student,
        'breadcrumb_title': 'Grades - Progress History',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/grades/grade_history.html', context)


# ========================
# COMMUNICATION SUB-DASHBOARD
# ========================

@teacher_required
def message_inbox(request):
    """
    Teacher message inbox with filter tabs (All, Unread, Received, Sent).
    
    Paginated view showing messages received by the teacher and messages sent by the teacher.
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    # Get filter type from GET param
    filter_type = request.GET.get('filter', 'all')
    page_num = request.GET.get('page', 1)
    
    # Build base queryset - messages where teacher is recipient
    received_messages = MessageRecipient.objects.filter(
        recipient=request.user,
        message__school=request.user.school
    ).select_related('message', 'message__sender').order_by('-created_at')
    
    # Apply filters and determine which queryset to use for pagination
    messages_to_paginate = received_messages
    if filter_type == 'unread':
        messages_to_paginate = received_messages.filter(read_at__isnull=True)
    elif filter_type == 'sent':
        # Messages sent by this teacher
        messages_to_paginate = Message.objects.filter(
            sender=request.user,
            school=request.user.school
        ).select_related('sender').order_by('-created_at')
    
    # Paginate
    paginator = Paginator(messages_to_paginate, 10)
    page_obj = paginator.get_page(page_num)
    
    # Count stats
    unread_count = MessageRecipient.objects.filter(
        recipient=request.user,
        read_at__isnull=True,
        message__school=request.user.school
    ).count()
    
    total_count = MessageRecipient.objects.filter(
        recipient=request.user,
        message__school=request.user.school
    ).count()
    
    nav_items = [
        {'label': 'Inbox', 'url': reverse('teacher:message_inbox'), 'icon': 'mail', 'is_active': request.path == '/teacher/communication/'},
    ]
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
        'unread_count': unread_count,
        'total_count': total_count,
        'breadcrumb_title': 'Communication - Inbox',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/communication/message_inbox.html', context)


@teacher_required
def message_detail(request, message_id):
    """
    Display single message with full content and reply functionality.
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    # Get the message, ensure teacher is recipient or sender
    message = get_object_or_404(
        Message.objects.select_related('sender'),
        id=message_id,
        school=request.user.school
    )
    
    # Check if teacher is a recipient of this message
    message_recipient = MessageRecipient.objects.filter(
        message=message,
        recipient=request.user
    ).first()
    
    if not message_recipient and message.sender != request.user:
        return redirect('teacher:message_inbox')
    
    # Mark as read if not already
    if message_recipient and not message_recipient.read_at:
        message_recipient.read_at = timezone.now()
        message_recipient.save()
    
    nav_items = [
        {'label': 'Inbox', 'url': reverse('teacher:message_inbox'), 'icon': 'mail', 'is_active': request.path == '/teacher/communication/'},
    ]
    
    context = {
        'message': message,
        'message_recipient': message_recipient,
        'breadcrumb_title': 'Communication - Message Detail',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/communication/message_detail.html', context)


@teacher_required
@require_http_methods(['POST'])
def send_message_ajax(request):
    """
    AJAX endpoint for sending messages from teacher to parents/colleagues/admin.
    
    POST params:
    - recipient_type: 'class_announcement', 'individual_parent', 'specific_teacher', 'admin'
    - target_class: (for class_announcement)
    - target_user: (for individual_parent or specific_teacher)
    - subject: Message subject
    - body: Message body
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return JsonResponse({'success': False, 'error': 'Teacher profile not found'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    recipient_type = data.get('recipient_type')
    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    
    # Validation
    if not subject or not body:
        return JsonResponse({
            'success': False,
            'error': 'Subject and body are required'
        }, status=400)
    
    if len(body) < 5:
        return JsonResponse({
            'success': False,
            'error': 'Message body must be at least 5 characters'
        }, status=400)
    
    # Create Message object
    message = Message.objects.create(
        sender=request.user,
        sender_type='teacher',
        school=request.user.school,
        subject=subject,
        body=body,
        recipient_type=recipient_type,
    )
    
    # Resolve recipients based on type
    if recipient_type == 'class_announcement':
        class_id = data.get('target_class')
        if not class_id:
            message.delete()
            return JsonResponse({
                'success': False,
                'error': 'Class not specified'
            }, status=400)
        message.target_class_id = class_id
        message.save()
        
        # Resolve: all parents of students in this class
        recipients = CustomUser.objects.filter(
            school=request.user.school,
            role='parent',
            children__class_grade_id=class_id,
            children__status='active'
        ).distinct()
        
    elif recipient_type == 'individual_parent':
        target_user_id = data.get('target_user')
        if not target_user_id:
            message.delete()
            return JsonResponse({
                'success': False,
                'error': 'Recipient not specified'
            }, status=400)
        message.target_user_id = target_user_id
        message.save()
        recipients = CustomUser.objects.filter(id=target_user_id)
        
    elif recipient_type == 'specific_teacher':
        target_user_id = data.get('target_user')
        if not target_user_id:
            message.delete()
            return JsonResponse({
                'success': False,
                'error': 'Recipient not specified'
            }, status=400)
        message.target_user_id = target_user_id
        message.save()
        recipients = CustomUser.objects.filter(id=target_user_id)
        
    elif recipient_type == 'admin':
        # Send to all admins in school
        recipients = CustomUser.objects.filter(
            school=request.user.school,
            role='admin'
        )
    else:
        message.delete()
        return JsonResponse({
            'success': False,
            'error': f'Unknown recipient type: {recipient_type}'
        }, status=400)
    
    # Create MessageRecipient entries
    message_recipients = [
        MessageRecipient(message=message, recipient=user)
        for user in recipients
    ]
    MessageRecipient.objects.bulk_create(message_recipients)
    
    # Mark message as sent
    message.is_sent = True
    message.save()
    
    # Log activity
    ActivityLog.objects.create(
        teacher=staff,
        school=request.user.school,
        activity_type='message',
        description=f'Sent message: {subject[:50]}',
        object_id=message.id
    )
    
    return JsonResponse({
        'success': True,
        'data': {
            'message_id': message.id,
            'recipient_count': len(message_recipients),
        }
    })


@teacher_required
@require_http_methods(['POST'])
def mark_message_read_ajax(request, message_id):
    """
    AJAX endpoint to mark a message as read.
    """
    message_recipient = get_object_or_404(
        MessageRecipient,
        message_id=message_id,
        recipient=request.user
    )
    
    if not message_recipient.read_at:
        message_recipient.read_at = timezone.now()
        message_recipient.save()
    
    return JsonResponse({'success': True})


# ========================
# ATTENDANCES SUB-DASHBOARD
# ========================

@teacher_required
def attendance_marking(request):
    """
    Attendance marking interface - quick checkbox interface for daily roster.
    
    GET: Show current class roster with checkboxes
    POST: Save attendance records
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    if request.method == 'GET':
        # Show class selector and student roster
        class_id = request.GET.get('class_id')
        selected_class = None
        students = None
        
        if class_id:
            selected_class = get_object_or_404(classes, id=class_id)
            students = Student.objects.filter(
                class_grade=selected_class,
                status='active'
            ).order_by('first_name', 'last_name')
            
            # Check if attendance already marked for today
            today = timezone.localdate()
            existing_attendance = StudentAttendance.objects.filter(
                student__in=students,
                date=today
            ).values_list('student_id', flat=True)
            
            students_marked = set(existing_attendance)
        else:
            students_marked = set()
        
        nav_items = [
            {'label': 'Mark Attendance', 'url': reverse('teacher:attendance_marking'), 'icon': 'event_available', 'is_active': request.path == '/teacher/attendances/'},
            {'label': 'History', 'url': reverse('teacher:attendance_history'), 'icon': 'history', 'is_active': request.path == '/teacher/attendances/history/'},
        ]
        
        context = {
            'classes': classes,
            'selected_class': selected_class,
            'students': students,
            'students_marked': students_marked,
            'today': timezone.localdate(),
            'breadcrumb_title': 'Attendance - Mark Students',
            'nav_items': nav_items,
        }
        
        return render(request, 'teacher/sub_dashboards/attendances/attendance_marking.html', context)
    
    elif request.method == 'POST':
        # Handle attendance marking POST (AJAX)
        return mark_attendance_ajax(request)


@teacher_required
@require_http_methods(['POST'])
def mark_attendance_ajax(request):
    """
    AJAX endpoint to save bulk attendance for a class.
    
    POST params (JSON):
    - class_id: ID of the class
    - attendance_data: { student_id: 'present'|'absent'|'late', ... }
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return JsonResponse({'success': False, 'error': 'Teacher profile not found'}, status=403)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    class_id = data.get('class_id')
    attendance_data = data.get('attendance_data', {})
    
    if not class_id or not attendance_data:
        return JsonResponse({
            'success': False,
            'error': 'Class ID and attendance data required'
        }, status=400)
    
    today = timezone.localdate()
    is_online = data.get('is_online', True)  # Detect if browser is online
    
    try:
        class_obj = ClassGrade.objects.get(id=class_id, school=request.user.school)
    except ClassGrade.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Class not found'}, status=404)
    
    # Create or update attendance records
    created_count = 0
    updated_count = 0
    
    for student_id_str, status in attendance_data.items():
        try:
            student_id = int(student_id_str)
            student = Student.objects.get(
                id=student_id,
                class_grade=class_obj
            )
            
            # Validate status
            valid_statuses = ['present', 'absent', 'late']
            if status not in valid_statuses:
                continue
            
            # Create or update attendance
            attendance, created = StudentAttendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'status': status,
                    'synced': is_online,  # Set synced based on online status
                }
            )
            
            if created:
                created_count += 1
            else:
                attendance.status = status
                attendance.synced = is_online
                attendance.save()
                updated_count += 1
        
        except (ValueError, Student.DoesNotExist):
            continue
    
    # Log activity
    ActivityLog.objects.create(
        teacher=staff,
        activity_type='attendance_marked',
        description=f'Marked attendance for {class_obj.name}: {created_count + updated_count} records',
        severity='success',
        icon_name='event_note'
    )
    
    return JsonResponse({
        'success': True,
        'data': {
            'created_count': created_count,
            'updated_count': updated_count,
            'total_marked': created_count + updated_count,
            'synced': is_online,
        }
    })


@teacher_required
def attendance_history(request):
    """
    Attendance history view - calendar/matrix with statistics.
    
    GET params:
    - class_id: Filter by class
    - student_id: Filter by individual student
    - start_date: Date range start (YYYY-MM-DD)
    - end_date: Date range end (YYYY-MM-DD)
    """
    staff = get_teacher_staff_profile(request)
    if not staff:
        return redirect('teacher:profile')
    
    classes = get_teacher_classes(staff)
    
    # Get filters
    class_id = request.GET.get('class_id')
    student_id = request.GET.get('student_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    selected_class = None
    selected_student = None
    attendance_records = None
    
    if class_id:
        selected_class = get_object_or_404(classes, id=class_id)
        
        # Parse date range
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = timezone.localdate() - timedelta(days=30)
        
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = timezone.localdate()
        
        # Fetch attendance records
        attendance_qs = StudentAttendance.objects.filter(
            student__class_grade=selected_class,
            date__range=[start_date, end_date]
        ).select_related('student').order_by('date', 'student__first_name')
        
        # Filter by student if specified
        if student_id:
            selected_student = get_object_or_404(
                Student.objects.filter(class_grade=selected_class),
                id=student_id
            )
            attendance_qs = attendance_qs.filter(student=selected_student)
        
        attendance_records = attendance_qs
    
    nav_items = [
        {'label': 'Mark Attendance', 'url': reverse('teacher:attendance_marking'), 'icon': 'event_available', 'is_active': request.path == '/teacher/attendances/'},
        {'label': 'History', 'url': reverse('teacher:attendance_history'), 'icon': 'history', 'is_active': request.path == '/teacher/attendances/history/'},
    ]
    
    context = {
        'classes': classes,
        'selected_class': selected_class,
        'selected_student': selected_student,
        'attendance_records': attendance_records,
        'breadcrumb_title': 'Attendance - View History',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/attendances/attendance_history.html', context)


# ========================
# GRADEBOOK REFERENCE
# ========================

@teacher_required
def gradebook_reference(request):
    """
    Static gradebook reference - Uganda national grading standards.
    
    Displays grade scale (A-F) with score ranges and descriptions.
    """
    # Uganda grading scale
    grading_scale = [
        {
            'grade': 'A',
            'min_score': 75,
            'max_score': 100,
            'description': 'Excellent',
            'color': '#10b981',  # green
        },
        {
            'grade': 'B',
            'min_score': 65,
            'max_score': 74,
            'description': 'Good',
            'color': '#3b82f6',  # blue
        },
        {
            'grade': 'C',
            'min_score': 50,
            'max_score': 64,
            'description': 'Satisfactory',
            'color': '#f59e0b',  # amber
        },
        {
            'grade': 'D',
            'min_score': 40,
            'max_score': 49,
            'description': 'Fair',
            'color': '#f97316',  # orange
        },
        {
            'grade': 'E',
            'min_score': 0,
            'max_score': 39,
            'description': 'Poor',
            'color': '#ef4444',  # red
        },
    ]
    
    nav_items = [
        {'label': 'Grading Scale', 'url': reverse('teacher:gradebook_reference'), 'icon': 'grade', 'is_active': request.path == '/teacher/gradebook/'},
    ]
    
    context = {
        'grading_scale': grading_scale,
        'breadcrumb_title': 'Gradebook - Uganda Grading Scale',
        'nav_items': nav_items,
    }
    
    return render(request, 'teacher/sub_dashboards/gradebook/gradebook_reference.html', context)


@teacher_required
@require_http_methods(['POST'])
def grade_lookup_ajax(request):
    """
    AJAX endpoint for score → grade lookup.
    
    POST params:
    - score: Numeric score (0-100)
    
    Returns: { grade, min_score, max_score, description }
    """
    try:
        data = json.loads(request.body)
        score = float(data.get('score'))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid score'}, status=400)
    
    if not 0 <= score <= 100:
        return JsonResponse({'error': 'Score must be between 0 and 100'}, status=400)
    
    # Determine grade
    if score >= 75:
        grade_data = {'grade': 'A', 'min': 75, 'max': 100, 'desc': 'Excellent', 'color': '#10b981'}
    elif score >= 65:
        grade_data = {'grade': 'B', 'min': 65, 'max': 74, 'desc': 'Good', 'color': '#3b82f6'}
    elif score >= 50:
        grade_data = {'grade': 'C', 'min': 50, 'max': 64, 'desc': 'Satisfactory', 'color': '#f59e0b'}
    elif score >= 40:
        grade_data = {'grade': 'D', 'min': 40, 'max': 49, 'desc': 'Fair', 'color': '#f97316'}
    else:
        grade_data = {'grade': 'E', 'min': 0, 'max': 39, 'desc': 'Poor', 'color': '#ef4444'}
    
    return JsonResponse({
        'success': True,
        'data': grade_data,
    })
