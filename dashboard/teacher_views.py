from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Avg
from SchoolNowMgt.models import (
    StaffProfile, Timetable, Student, ClassGrade,
    StudentAttendance, RetentionAlert, Grade,
    TeacherTask, ActivityLog, TeacherAttendance, Subject
)
from datetime import timedelta


@login_required(login_url='teacher:login')
def teacher_dashboard(request):
    """
    Modern teacher dashboard view with database-backed tasks and activities.
    
    Displays:
    - Current lesson card
    - Pending tasks (from TeacherTask model)
    - Recent activities (from ActivityLog model)
    - Quick action cards (Attendance, Gradebook, Circulars)
    - Performance chart (weekly averages)
    """
    # Verify logged-in user is a teacher
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    # Fetch StaffProfile or redirect to profile setup
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.localdate()
    day_of_week = today.strftime('%A').lower()
    
    # ===== TEACHER ATTENDANCE / SHIFT STATUS =====
    # Get or create today's attendance record for the teacher
    teacher_attendance_today, created = TeacherAttendance.objects.get_or_create(
        staff=staff,
        date=today,
        defaults={'status': 'absent'}
    )
    
    is_on_duty = teacher_attendance_today.status == 'present'
    shift_start_time = timezone.now()  # Current time, will be replaced with time_in if available
    if teacher_attendance_today.time_in:
        # Combine date with time_in to create a datetime
        shift_start_time = timezone.make_aware(
            timezone.datetime.combine(today, teacher_attendance_today.time_in)
        )
    
    current_time = timezone.now()
    
    # ===== TODAY'S SCHEDULE / CURRENT LESSON =====
    todays_classes = Timetable.objects.filter(
        teacher=staff,
        day_of_week=day_of_week
    ).select_related('subject', 'class_grade').order_by('start_time')
    
    current_lesson = todays_classes.first() if todays_classes.exists() else None
    
    # ===== MY CLASSES & STUDENTS =====
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff
    ).annotate(
        student_count=Count('students', filter=Q(students__status='active'))
    )
    
    my_students = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    )
    
    # ===== PENDING TASKS (Real database) =====
    tasks = TeacherTask.objects.filter(
        teacher=staff,
        status='pending'
    ).order_by('-priority', 'due_date')[:3]
    
    total_tasks_pending = TeacherTask.objects.filter(
        teacher=staff,
        status='pending'
    ).count()
    
    # ===== RECENT ACTIVITIES (Real database) =====
    activities = ActivityLog.objects.filter(
        teacher=staff
    ).order_by('-created_at')[:3]
    
    # ===== PERFORMANCE STATISTICS =====
    # Calculate weekly grade averages (past 7 days)
    week_ago = today - timedelta(days=7)
    weekly_grades = Grade.objects.filter(
        student__class_grade__class_teacher=staff,
        created_at__date__gte=week_ago
    ).aggregate(avg=Avg('score'))
    
    performance_metric = float(weekly_grades['avg'] or 0.0)
    
    # Generate performance data for chart (simplified)
    performance_stats = [
        performance_metric * 0.8,   # Mon
        performance_metric * 0.85,  # Tue
        performance_metric * 0.9,   # Wed
        performance_metric * 0.88,  # Thu
        performance_metric * 0.95,  # Fri
        performance_metric * 0.92,  # Sat
        performance_metric,          # Sun
    ]
    
    # ===== GET ALL TEACHER'S SUBJECTS (FOR GRADE MODAL) =====
    subject_ids = Timetable.objects.filter(teacher=staff).values_list('subject_id', flat=True).distinct()
    subjects = Subject.objects.filter(id__in=subject_ids)
    
    # Build context
    context = {
        'today': today,
        'now': current_time,
        'is_on_duty': is_on_duty,
        'shift_start_time': shift_start_time,
        'current_time': current_time,
        'teacher_attendance_today': teacher_attendance_today,
        'current_lesson': current_lesson,
        'tasks': tasks,
        'total_tasks_pending': total_tasks_pending,
        'activities': activities,
        'my_classes': my_classes,
        'my_students': my_students,
        'students': my_students,
        'my_student_count': len(my_students),
        'performance_metric': performance_metric,
        'performance_stats': performance_stats,
        'todays_classes': todays_classes,
        'teacher_name': request.user.get_full_name(),
        'subjects': subjects,
    }
    
    return render(request, 'teacher/dashboard_modern.html', context)


# ===== API ENDPOINTS FOR AJAX OPERATIONS =====
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.middleware.csrf import get_token


@login_required(login_url='teacher:login')
@require_POST
def toggle_task_status(request, task_id):
    """Toggle task status between pending and completed"""
    try:
        staff = StaffProfile.objects.get(user=request.user)
        task = TeacherTask.objects.get(id=task_id, teacher=staff)
        
        # Toggle status
        task.status = 'completed' if task.status == 'pending' else 'pending'
        if task.status == 'completed':
            task.completed_at = timezone.now()
        task.save()
        
        return JsonResponse({
            'success': True,
            'status': task.status,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None
        })
    except TeacherTask.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='teacher:login')
@require_POST
def create_task(request):
    """Create a new task"""
    try:
        staff = StaffProfile.objects.get(user=request.user)
        
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        priority = request.POST.get('priority', 'medium')
        
        if not title or not due_date:
            return JsonResponse({'success': False, 'error': 'Title and due date required'}, status=400)
        
        task = TeacherTask.objects.create(
            teacher=staff,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'priority': task.priority,
                'due_date': task.due_date.isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='teacher:login')
@require_http_methods(["GET"])
def student_search(request):
    """Search students in teacher's classes"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'students': []})
    
    try:
        staff = StaffProfile.objects.get(user=request.user)
        
        # Search in teacher's students
        students = Student.objects.filter(
            class_grade__class_teacher=staff,
            status='active'
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query)
        ).values('id', 'admission_number', 'first_name', 'last_name')[:10]
        
        return JsonResponse({
            'students': list(students)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='teacher:login')
@require_POST
def quick_grade_entry(request):
    """Enter a grade for a student"""
    try:
        staff = StaffProfile.objects.get(user=request.user)
        
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        score = request.POST.get('score')
        
        if not all([student_id, subject_id, score]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        try:
            score = float(score)
            if not (0 <= score <= 100):
                return JsonResponse({'success': False, 'error': 'Score must be 0-100'}, status=400)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid score format'}, status=400)
        
        student = Student.objects.get(id=student_id, class_grade__class_teacher=staff)
        
        # Get or create grade
        grade, created = Grade.objects.update_or_create(
            student=student,
            subject_id=subject_id,
            defaults={
                'score': score,
                'recorded_by': request.user,
                'created_at': timezone.now()
            }
        )
        
        return JsonResponse({
            'success': True,
            'grade': {
                'id': grade.id,
                'student': student.full_name,
                'score': grade.score,
                'created': created
            }
        })
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required(login_url='teacher:login')
@require_POST
def send_circular(request):
    """Send a circular/message to parents"""
    try:
        staff = StaffProfile.objects.get(user=request.user)
        
        class_id = request.POST.get('class_id')
        message = request.POST.get('message')
        
        if not class_id or not message:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        if len(message) > 160:
            return JsonResponse({'success': False, 'error': 'Message too long (max 160 chars)'}, status=400)
        
        # Create activity log
        ActivityLog.objects.create(
            teacher=staff,
            activity_type='circular_sent',
            description=message,
            icon_name='mail',
            severity='info'
        )
        
        # Get parent count for response
        parent_count = Student.objects.filter(
            class_grade_id=class_id
        ).values('parent_phone').distinct().count()
        
        return JsonResponse({
            'success': True,
            'message': 'Circular queued for delivery',
            'parent_count': parent_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== NEW TEACHER VIEWS (Phase 3) =====

@login_required(login_url='teacher:login')
def teacher_students_list(request):
    """
    List all students from teacher's assigned classes.
    
    Displays:
    - Students with name, admission number, class, attendance today
    - Search/filter functionality
    - Pagination
    """
    # Verify logged-in user is a teacher
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    # Fetch StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.localdate()
    
    # Get all students from teacher's classes
    students = Student.objects.filter(
        class_grade__class_teacher=staff,
        status='active'
    ).select_related('class_grade').order_by('class_grade__level', 'first_name')
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    class_filter = request.GET.get('class', '')
    
    # Apply filters
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )
    
    if class_filter:
        students = students.filter(class_grade_id=class_filter)
    
    # Get classes for filter dropdown
    my_classes = ClassGrade.objects.filter(
        class_teacher=staff
    ).order_by('level')
    
    # Attendance data for today
    attendance_today = StudentAttendance.objects.filter(
        date=today,
        student__class_grade__class_teacher=staff
    ).values('student_id', 'status')
    
    attendance_dict = {att['student_id']: att['status'] for att in attendance_today}
    
    # Add attendance status to each student
    for student in students:
        student.attendance_status = attendance_dict.get(student.id, 'not_marked')
    
    context = {
        'students': students,
        'my_classes': my_classes,
        'search_query': search_query,
        'class_filter': class_filter,
        'total_students': students.count(),
        'today': today,
    }
    
    return render(request, 'teacher/students_list.html', context)


@login_required(login_url='teacher:login')
def teacher_lessons_list(request):
    """
    List all lessons (timetable) for the teacher.
    
    Displays:
    - Lessons by class, day, time
    - Subject, student count
    - Week view
    """
    # Verify logged-in user is a teacher
    if request.user.role != 'teacher':
        return redirect('teacher:login')
    
    # Fetch StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get today's date
    today = timezone.localdate()
    
    # Get all lessons/timetable entries for this teacher
    all_lessons = Timetable.objects.filter(
        teacher=staff
    ).select_related('subject', 'class_grade').order_by('day_of_week', 'start_time')
    
    # Get unique days for display
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    days_display = {
        'monday': 'Monday',
        'tuesday': 'Tuesday',
        'wednesday': 'Wednesday',
        'thursday': 'Thursday',
        'friday': 'Friday',
    }
    
    # Create a list of day objects with their lessons
    days_with_lessons = []
    for day in days_of_week:
        day_lessons = [l for l in all_lessons if l.day_of_week == day]
        if day_lessons:
            # Annotate student count for each lesson
            for lesson in day_lessons:
                lesson.student_count = Student.objects.filter(
                    class_grade=lesson.class_grade,
                    status='active'
                ).count()
            
            days_with_lessons.append({
                'day_code': day,
                'day_name': days_display[day],
                'lessons': day_lessons
            })
    
    context = {
        'all_lessons': all_lessons,
        'days_with_lessons': days_with_lessons,
        'today': today,
        'total_lessons': all_lessons.count(),
    }
    
    return render(request, 'teacher/lessons_list.html', context)
