from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.contrib import messages
from django.http import JsonResponse
from .forms import TeacherLoginForm, TeacherRegistrationForm
from SchoolNowMgt.models import (
    StaffProfile, Timetable, Student, ClassGrade,
    StudentAttendance, RetentionAlert, Grade, TeacherTask, ActivityLog, Subject
)


def teacher_register(request):
    """
    Teacher registration view - redirects to unified registration.
    """
    return redirect('auth:unified_register')


def teacher_login(request):
    """
    Teacher login view - redirects to unified login.
    """
    return redirect('auth:unified_login')


@login_required(login_url='teacher:login')
@require_POST
def teacher_logout(request):
    """
    Teacher logout view. POST only.
    """
    logout(request)
    return redirect('auth:unified_login')


@login_required(login_url='teacher:login')
def teacher_dashboard(request):
    """
    Teacher dashboard view.
    
    Displays:
    - Welcome banner (first login only)
    - Today's schedule
    - My students and classes
    - Attendance overview (my classes)
    - At-risk students (my classes)
    - Recent grades entered by this teacher
    """
    # Verify logged-in user is a teacher
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    # Fetch StaffProfile or redirect to profile setup
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.localtime()
    current_time = timezone.now()
    
    # Determine first login (banner display logic)
    is_first_login = (
        request.user.last_login is None or 
        request.user.date_joined.date() == today.date()
    )
    
    # Convert today to lowercase day name (e.g., "monday")
    day_of_week = today.strftime('%A').lower()
    
    # ===== TODAY'S SCHEDULE =====
    todays_classes = Timetable.objects.filter(
        teacher=staff,
        day_of_week=day_of_week
    ).select_related('subject', 'class_grade').order_by('start_time')
    
    # Get current lesson (first class today)
    current_lesson = todays_classes.first()
    
    # ===== MY STUDENTS =====
    my_student_count = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    ).count()
    
    my_students = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    )[:4]
    
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    )
    
    # ===== ATTENDANCE — MY CLASSES TODAY =====
    attendance_marked_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date()
    ).exists()
    
    present_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date(),
        status='present'
    ).count()
    
    absent_today = StudentAttendance.objects.filter(
        student__class_grade__class_teacher=staff,
        date=today.date(),
        status='absent'
    ).count()
    
    # ===== AT-RISK STUDENTS (MY CLASSES ONLY) =====
    at_risk_alerts = RetentionAlert.objects.filter(
        student__class_grade__class_teacher=staff,
        resolved=False
    ).select_related('student').order_by('-created_at')[:5]
    
    at_risk_count = RetentionAlert.objects.filter(
        student__class_grade__class_teacher=staff,
        resolved=False
    ).count()
    
    # ===== RECENT GRADES (ENTERED BY THIS TEACHER) =====
    recent_grades = Grade.objects.filter(
        recorded_by=request.user
    ).select_related('student', 'subject').order_by('-created_at')[:5]
    
    # ===== TASK PRIORITY WIDGET =====
    # Get pending tasks (max 3)
    priority_tasks = TeacherTask.objects.filter(
        teacher=staff,
        status='pending'
    ).select_related('subject', 'class_grade').order_by('-priority', 'due_date')[:3]
    
    # Count total pending tasks
    total_tasks_pending = TeacherTask.objects.filter(
        teacher=staff,
        status='pending'
    ).count()
    
    # ===== RECENT ACTIVITY =====
    # Get recent activities (max 3)
    recent_activities = ActivityLog.objects.filter(
        teacher=staff
    ).select_related('related_student').order_by('-created_at')[:3]
    
    # ===== PERFORMANCE STATS - WEEKLY AVERAGE =====
    # Calculate weekly average scores for students in teacher's classes
    from datetime import timedelta
    seven_days_ago = today - timedelta(days=7)
    
    weekly_grades = Grade.objects.filter(
        student__class_grade__class_teacher=staff,
        created_at__gte=seven_days_ago
    ).values('created_at__date').annotate(
        daily_avg=Avg('score')
    ).order_by('created_at__date')
    
    performance_stats = []
    if weekly_grades:
        max_score = max(g['daily_avg'] for g in weekly_grades) or 100
        for grade in weekly_grades:
            height = int((grade['daily_avg'] / max_score) * 100) if max_score > 0 else 0
            performance_stats.append({'height': height, 'score': round(grade['daily_avg'], 1)})
    else:
        # Placeholder if no grades
        performance_stats = [{'height': h, 'score': h} for h in [60, 75, 85, 95, 70]]
    
    # Calculate overall average for display
    overall_avg = Grade.objects.filter(
        student__class_grade__class_teacher=staff,
        created_at__gte=seven_days_ago
    ).aggregate(avg=Avg('score'))['avg']
    
    if overall_avg:
        performance_metric = f"{round(overall_avg, 1)}% average"
    else:
        performance_metric = "No data"
    
    # ===== GET ALL TEACHER'S SUBJECTS (FOR GRADE MODAL) =====
    subject_ids = Timetable.objects.filter(teacher=staff).values_list('subject_id', flat=True).distinct()
    subjects = Subject.objects.filter(id__in=subject_ids)
    
    # Build context
    context = {
        'today': today,
        'current_time': current_time,
        'is_first_login': is_first_login,
        'employee_id': staff.employee_id,
        'todays_classes': todays_classes,
        'current_lesson': current_lesson if current_lesson else {'subject': 'No Lesson', 'description': 'No active lesson at this time'},
        'my_student_count': my_student_count,
        'students': my_students,
        'my_classes': my_classes,
        'attendance_marked_today': attendance_marked_today,
        'present_today': present_today,
        'absent_today': absent_today,
        'at_risk_alerts': at_risk_alerts,
        'at_risk_count': at_risk_count,
        'recent_grades': recent_grades,
        'tasks': priority_tasks,
        'total_tasks_pending': total_tasks_pending,
        'activities': recent_activities,
        'performance_stats': performance_stats,
        'performance_metric': performance_metric,
        'subjects': subjects,
    }
    
    return render(request, 'teacher/dashboard_modern.html', context)


# ===== API ENDPOINTS FOR AJAX CALLS =====

@login_required(login_url='teacher:login')
@require_POST
def toggle_task_status(request, task_id):
    """
    AJAX endpoint to toggle task completion status.
    Expects POST request with optional 'status' parameter (pending/completed).
    Returns JSON with success status and new task status.
    """
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    try:
        staff = StaffProfile.objects.get(user=request.user)
        task = TeacherTask.objects.get(id=task_id, teacher=staff)
        
        # Toggle status
        if request.POST.get('status') == 'completed' or task.status == 'pending':
            task.status = 'completed' if task.status == 'pending' else 'pending'
            task.completed_at = timezone.now() if task.status == 'completed' else None
            task.save()
        
        return JsonResponse({
            'success': True,
            'new_status': task.status,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        })
    except TeacherTask.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='teacher:login')
@require_POST
def create_task(request):
    """
    AJAX endpoint to create a new task.
    Expects POST data: title, description, due_date, priority, subject_id, class_id
    Returns JSON with created task details.
    """
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    try:
        staff = StaffProfile.objects.get(user=request.user)
        
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority', 'medium')
        subject_id = request.POST.get('subject_id')
        class_id = request.POST.get('class_id')
        
        if not title or not due_date:
            return JsonResponse({
                'success': False,
                'error': 'Title and due date are required'
            }, status=400)
        
        task = TeacherTask.objects.create(
            teacher=staff,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            subject_id=subject_id if subject_id else None,
            class_id=class_id if class_id else None,
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'priority': task.priority,
                'due_date': task.due_date.isoformat(),
                'status': task.status,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='teacher:login')
def student_search(request):
    """
    AJAX endpoint to search students in teacher's classes.
    Query parameter: q (search term)
    Returns JSON list of matching students.
    """
    if request.user.role != 'teacher':
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        staff = StaffProfile.objects.get(user=request.user)
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return JsonResponse({'results': []})
        
        students = Student.objects.filter(
            class_grade__class_teacher=staff,
            status='active'
        ).filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query)
        ).values('id', 'first_name', 'last_name', 'admission_number', 'class_grade__name')[:10]
        
        results = [
            {
                'id': s['id'],
                'name': f"{s['first_name']} {s['last_name']}",
                'admission_number': s['admission_number'],
                'class': s['class_grade__name']
            }
            for s in students
        ]
        
        return JsonResponse({'results': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='teacher:login')
@require_POST
def quick_grade_entry(request):
    """
    AJAX endpoint to quickly enter a single grade.
    Expects POST data: student_id, subject_id, term, score
    Returns JSON with success status and grade details.
    """
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    try:
        from datetime import datetime
        
        staff = StaffProfile.objects.get(user=request.user)
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        term = request.POST.get('term', 'term_1')
        score = request.POST.get('score')
        academic_year = datetime.now().year
        
        if not all([student_id, subject_id, score]):
            return JsonResponse({
                'success': False,
                'error': 'Student, subject, and score are required'
            }, status=400)
        
        try:
            score = float(score)
            if not (0 <= score <= 100):
                return JsonResponse({
                    'success': False,
                    'error': 'Score must be between 0 and 100'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Score must be a number'
            }, status=400)
        
        student = Student.objects.get(
            id=student_id,
            class_grade__class_teacher=staff
        )
        
        grade, created = Grade.objects.update_or_create(
            student=student,
            subject_id=subject_id,
            term=term,
            academic_year=academic_year,
            defaults={'score': score, 'recorded_by': request.user}
        )
        
        return JsonResponse({
            'success': True,
            'grade': {
                'id': grade.id,
                'student': str(student),
                'score': grade.score,
                'created': created
            }
        })
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found or not in your class'
        }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required(login_url='teacher:login')
@require_POST
def send_circular(request):
    """
    AJAX endpoint to send circular SMS/Email to parents.
    Expects POST data: message, class_id, delivery_method (sms/email)
    Returns JSON with success status and delivery details.
    """
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    try:
        staff = StaffProfile.objects.get(user=request.user)
        message = request.POST.get('message', '').strip()
        class_id = request.POST.get('class_id')
        delivery_method = request.POST.get('delivery_method', 'sms')
        
        if not message or not class_id:
            return JsonResponse({
                'success': False,
                'error': 'Message and class are required'
            }, status=400)
        
        class_grade = ClassGrade.objects.get(id=class_id, class_teacher=staff)
        
        # Get all active students in the class
        students = Student.objects.filter(
            class_grade=class_grade,
            status='active'
        )
        
        # Count parents to notify (would integrate with SMS/Email service here)
        parent_count = students.count()
        
        # TODO: Integrate with SMS/Email service to actually send
        # For now, log the circular request
        ActivityLog.objects.create(
            teacher=staff,
            activity_type='circular_sent',
            description=f"Circular sent to {parent_count} parents of {class_grade.name}",
            icon_name='mail',
            severity='success'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Circular queued for delivery to {parent_count} parent(s)',
            'parent_count': parent_count
        })
    except ClassGrade.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Class not found or you are not the class teacher'
        }, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
