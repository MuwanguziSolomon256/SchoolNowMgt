"""
AJAX endpoints for teacher shift management (clock in/out, breaks).

Handles real-time shift tracking with validation, error handling,
and response formatting for the teacher dashboard frontend.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, time, timedelta
from django.db import transaction
import json

from SchoolNowMgt.models import TeacherAttendance, BreakSession, StaffProfile


def get_current_time_in_timezone():
    """
    Get the current time in the configured Django timezone (Africa/Kampala).
    
    timezone.localtime() converts UTC to the configured TIME_ZONE setting,
    which is the proper way to get local time when USE_TZ=True.
    """
    from django.utils.timezone import localtime
    
    # Get current UTC datetime and convert to local timezone
    local_datetime = localtime(timezone.now())
    
    # Return just the time component
    return local_datetime.time()


def get_teacher_profile(user):
    """
    Get teacher's StaffProfile or return error response.
    Used across all shift endpoints.
    """
    try:
        staff_profile = StaffProfile.objects.get(user=user, user__role='teacher')
        return staff_profile, None
    except StaffProfile.DoesNotExist:
        return None, JsonResponse(
            {'success': False, 'error': 'Teacher profile not found'},
            status=400
        )


def get_or_create_today_attendance(staff_profile):
    """
    Get or create today's TeacherAttendance record.
    Returns (attendance, created, error_response).
    """
    today = timezone.now().date()
    try:
        attendance, created = TeacherAttendance.objects.get_or_create(
            staff=staff_profile,
            date=today,
            defaults={'status': 'present'}
        )
        return attendance, created, None
    except Exception as e:
        error_response = JsonResponse(
            {'success': False, 'error': f'Database error: {str(e)}'},
            status=500
        )
        return None, None, error_response


@login_required
@require_POST
def clock_in(request):
    """
    AJAX endpoint: POST /teacher/api/shift/clock-in/
    
    Teacher clocks in to start their shift.
    
    Response:
        {
            'success': bool,
            'message': str,
            'time_in': 'HH:MM' (only if success),
            'shift_id': int (only if success),
            'error': str (only if failed)
        }
    """
    staff_profile, error = get_teacher_profile(request.user)
    if error:
        return error
    
    # Get or create today's attendance record
    attendance, created, error = get_or_create_today_attendance(staff_profile)
    if error:
        return error
    
    # Validate: prevent double clock-in
    if attendance.time_in is not None and attendance.time_out is None:
        return JsonResponse({
            'success': False,
            'error': 'Already clocked in. Please clock out first.',
        }, status=400)
    
    # If clocked out today, don't allow clock in again (same shift day)
    if attendance.time_out is not None:
        return JsonResponse({
            'success': False,
            'error': 'Already clocked out today. New shift can only start tomorrow.',
        }, status=400)
    
    try:
        with transaction.atomic():
            # Set clock-in time - using the correct local timezone
            current_time = get_current_time_in_timezone()
            attendance.time_in = current_time
            attendance.status = 'present'
            attendance.synced = False  # Mark for offline sync
            attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Clocked in at {current_time.strftime("%H:%M")}',
                'time_in': current_time.strftime("%H:%M"),
                'shift_id': attendance.id,
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to clock in: {str(e)}',
        }, status=500)


@login_required
@require_POST
def clock_out(request):
    """
    AJAX endpoint: POST /teacher/api/shift/clock-out/
    
    Teacher clocks out to end their shift.
    
    Response:
        {
            'success': bool,
            'message': str,
            'time_out': 'HH:MM' (only if success),
            'total_hours_worked': 'XhYm' (only if success),
            'break_count': int (only if success),
            'error': str (only if failed)
        }
    """
    staff_profile, error = get_teacher_profile(request.user)
    if error:
        return error
    
    # Get today's attendance record
    attendance, created, error = get_or_create_today_attendance(staff_profile)
    if error:
        return error
    
    # Validate: must be clocked in
    if attendance.time_in is None:
        return JsonResponse({
            'success': False,
            'error': 'Not clocked in. Please clock in first.',
        }, status=400)
    
    # Validate: prevent double clock-out
    if attendance.time_out is not None:
        return JsonResponse({
            'success': False,
            'error': 'Already clocked out today.',
        }, status=400)
    
    try:
        with transaction.atomic():
            # Close any active break sessions
            active_breaks = BreakSession.objects.filter(
                teacher_attendance=attendance,
                break_out_time__isnull=True
            )
            
            current_time = get_current_time_in_timezone()
            for break_session in active_breaks:
                break_session.break_out_time = current_time
                break_session.save()
                
                # Update total_break_duration
                duration = break_session.get_break_duration()
                if duration:
                    attendance.total_break_duration += duration
            
            # Set clock-out time
            attendance.time_out = current_time
            attendance.synced = False  # Mark for offline sync
            attendance.save()
            
            # Calculate shift hours
            shift_duration = attendance.get_shift_duration()
            hours = shift_duration // 60
            minutes = shift_duration % 60
            
            return JsonResponse({
                'success': True,
                'message': f'Clocked out at {current_time.strftime("%H:%M")}',
                'time_out': current_time.strftime("%H:%M"),
                'total_hours_worked': f"{hours}h {minutes}m",
                'break_count': attendance.break_count,
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to clock out: {str(e)}',
        }, status=500)


@login_required
@require_POST
def break_start(request):
    """
    AJAX endpoint: POST /teacher/api/shift/break-start/
    
    Teacher starts a break during their shift.
    
    Request body (optional):
        {
            'reason': str  # e.g., 'lunch', 'restroom', 'personal'
        }
    
    Response:
        {
            'success': bool,
            'message': str,
            'break_id': int (only if success),
            'break_in_time': 'HH:MM' (only if success),
            'error': str (only if failed)
        }
    """
    import json
    
    staff_profile, error = get_teacher_profile(request.user)
    if error:
        return error
    
    # Get today's attendance record
    attendance, created, error = get_or_create_today_attendance(staff_profile)
    if error:
        return error
    
    # Validate: must be clocked in
    if attendance.time_in is None:
        return JsonResponse({
            'success': False,
            'error': 'Not clocked in. Cannot take a break.',
        }, status=400)
    
    # Validate: must not be clocked out
    if attendance.time_out is not None:
        return JsonResponse({
            'success': False,
            'error': 'Already clocked out. Cannot take a break.',
        }, status=400)
    
    # Validate: no active break
    active_break = BreakSession.objects.filter(
        teacher_attendance=attendance,
        break_out_time__isnull=True
    ).first()
    
    if active_break:
        return JsonResponse({
            'success': False,
            'error': 'Already on break. Please end the current break first.',
        }, status=400)
    
    try:
        with transaction.atomic():
            # Get optional break reason from request body
            try:
                body = json.loads(request.body)
                reason = body.get('reason', '')
            except (json.JSONDecodeError, AttributeError):
                reason = ''
            
            # Create break session
            current_time = get_current_time_in_timezone()
            break_session = BreakSession.objects.create(
                teacher_attendance=attendance,
                break_in_time=current_time,
                reason=reason
            )
            
            # Increment break count
            attendance.break_count += 1
            attendance.synced = False
            attendance.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Break started at {current_time.strftime("%H:%M")}',
                'break_id': break_session.id,
                'break_in_time': current_time.strftime("%H:%M"),
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to start break: {str(e)}',
        }, status=500)


@login_required
@require_POST
def break_end(request):
    """
    AJAX endpoint: POST /teacher/api/shift/break-end/
    
    Teacher ends a break and resumes work.
    
    Response:
        {
            'success': bool,
            'message': str,
            'break_duration': 'XhYm' (only if success),
            'total_break_so_far': 'XhYm' (only if success),
            'error': str (only if failed)
        }
    """
    staff_profile, error = get_teacher_profile(request.user)
    if error:
        return error
    
    # Get today's attendance record
    attendance, created, error = get_or_create_today_attendance(staff_profile)
    if error:
        return error
    
    # Get active break session
    active_break = BreakSession.objects.filter(
        teacher_attendance=attendance,
        break_out_time__isnull=True
    ).first()
    
    if not active_break:
        return JsonResponse({
            'success': False,
            'error': 'No active break to end.',
        }, status=400)
    
    try:
        with transaction.atomic():
            # Close the break session
            current_time = get_current_time_in_timezone()
            active_break.break_out_time = current_time
            active_break.save()
            
            # Calculate break duration
            break_duration = active_break.get_break_duration()
            if break_duration:
                attendance.total_break_duration += break_duration
            
            attendance.synced = False
            attendance.save()
            
            # Format durations for response
            break_hours = break_duration // 60
            break_mins = break_duration % 60
            
            total_hours = attendance.total_break_duration // 60
            total_mins = attendance.total_break_duration % 60
            
            return JsonResponse({
                'success': True,
                'message': f'Break ended at {current_time.strftime("%H:%M")}',
                'break_duration': f"{break_hours}h {break_mins}m",
                'total_break_so_far': f"{total_hours}h {total_mins}m",
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to end break: {str(e)}',
        }, status=500)


@login_required
@require_GET
def shift_status(request):
    """
    AJAX endpoint: GET /teacher/api/shift/status/
    
    Returns current shift status for the teacher dashboard real-time updates.
    Used by frontend to refresh timer and break information.
    
    Response:
        {
            'success': bool,
            'is_on_duty': bool,
            'is_on_break': bool,
            'shift_start_time': 'HH:MM' (only if on duty),
            'shift_elapsed_minutes': int (only if on duty),
            'active_break_id': int (only if on break),
            'break_start_time': 'HH:MM' (only if on break),
            'break_elapsed_minutes': int (only if on break),
            'breaks_count': int (only if on duty),
            'total_break_minutes': int (only if on duty),
            'error': str (only if failed)
        }
    """
    staff_profile, error = get_teacher_profile(request.user)
    if error:
        return error
    
    today = timezone.now().date()
    try:
        attendance = TeacherAttendance.objects.filter(
            staff=staff_profile,
            date=today
        ).first()
        
        if not attendance or not attendance.time_in:
            # Not clocked in
            return JsonResponse({
                'success': True,
                'is_on_duty': False,
                'is_on_break': False,
            })
        
        # Calculate shift elapsed time
        current_time = timezone.now().time()
        current_datetime = datetime.combine(today, current_time)
        shift_start = datetime.combine(today, attendance.time_in)
        shift_elapsed = int((current_datetime - shift_start).total_seconds() / 60)
        
        # Check for active break
        active_break = BreakSession.objects.filter(
            teacher_attendance=attendance,
            break_out_time__isnull=True
        ).first()
        
        response = {
            'success': True,
            'is_on_duty': True,
            'is_on_break': bool(active_break),
            'shift_start_time': attendance.time_in.strftime("%H:%M"),
            'shift_elapsed_minutes': shift_elapsed,
            'breaks_count': attendance.break_count,
            'total_break_minutes': attendance.total_break_duration,
        }
        
        if active_break:
            current_break_start = datetime.combine(today, active_break.break_in_time)
            break_elapsed = int((current_datetime - current_break_start).total_seconds() / 60)
            response['active_break_id'] = active_break.id
            response['break_start_time'] = active_break.break_in_time.strftime("%H:%M")
            response['break_elapsed_minutes'] = break_elapsed
        
        return JsonResponse(response)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to get shift status: {str(e)}',
        }, status=500)
