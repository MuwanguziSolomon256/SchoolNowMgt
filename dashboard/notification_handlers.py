"""
Notification Handlers & API Endpoints

Provides:
1. Notification trigger functions (called when events occur)
2. AJAX endpoints for real-time notification fetching
3. Notification management (mark as read, delete, etc.)
4. Parent notification dashboard

This module handles:
- Creating notifications when grades posted
- Creating notifications when payments due/overdue
- Creating attendance alerts
- Sending notification emails (optional)
- AJAX API for notification badge + dropdown
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods

from SchoolNowMgt.models import Notification, CustomUser, StudentParentRelationship
from SchoolNowMgt.decorators import require_parent


# ============================================================================
# NOTIFICATION TRIGGER FUNCTIONS (Called by other modules)
# ============================================================================

def notify_parents_grade_posted(grade):
    """
    Create notifications for all parents when a grade is posted.
    
    Called by: Gradebook views when teacher posts a grade
    Created notifications: One per parent for each grade
    """
    try:
        student = grade.student
        school = student.school
        
        # Get all active parents for this student
        parent_relationships = StudentParentRelationship.objects.filter(
            student=student,
            school=school,
            is_active=True
        ).select_related('parent')
        
        notifications_created = 0
        for rel in parent_relationships:
            # Create notification
            Notification.create_grade_notification(rel.parent, grade)
            notifications_created += 1
        
        return notifications_created
    
    except Exception as e:
        print(f"Error notifying parents of grade: {e}")
        return 0


def notify_parents_payment_alert(student, alert_type='due'):
    """
    Create notifications for all parents about payment.
    
    Called by: Finance/payment views
    alert_type: 'due' or 'overdue'
    """
    try:
        school = student.school
        
        # Get all active parents
        parent_relationships = StudentParentRelationship.objects.filter(
            student=student,
            school=school,
            is_active=True
        ).select_related('parent')
        
        # Find latest fee payment for this student
        from SchoolNowMgt.models import FeePayment
        fee_payment = FeePayment.objects.filter(student=student).order_by('-due_date').first()
        
        if not fee_payment:
            return 0
        
        notifications_created = 0
        for rel in parent_relationships:
            Notification.create_payment_notification(rel.parent, fee_payment, alert_type)
            notifications_created += 1
        
        return notifications_created
    
    except Exception as e:
        print(f"Error notifying parents of payment: {e}")
        return 0


def notify_parents_attendance_alert(student, absent_days):
    """
    Create notifications for all parents about low attendance.
    
    Called by: Attendance tracking views
    """
    try:
        school = student.school
        
        # Get all active parents
        parent_relationships = StudentParentRelationship.objects.filter(
            student=student,
            school=school,
            is_active=True
        ).select_related('parent')
        
        notifications_created = 0
        for rel in parent_relationships:
            Notification.create_attendance_alert(rel.parent, student, absent_days)
            notifications_created += 1
        
        return notifications_created
    
    except Exception as e:
        print(f"Error notifying parents of attendance: {e}")
        return 0


def notify_user_new_message(recipient, sender, message_obj):
    """
    Create notification when user receives a message.
    
    Called by: Messaging views when message is sent
    """
    try:
        Notification.create_message_notification(recipient, sender, message_obj)
        return 1
    except Exception as e:
        print(f"Error creating message notification: {e}")
        return 0


# ============================================================================
# AJAX ENDPOINTS FOR REAL-TIME NOTIFICATIONS
# ============================================================================

@login_required
def get_notifications_ajax(request):
    """
    Get unread notifications for current user (AJAX endpoint).
    
    Returns:
    {
        'unread_count': int,
        'notifications': [
            {
                'id': int,
                'title': str,
                'message': str,
                'type': str,
                'created_at': ISO datetime,
                'action_url': str or null,
                'icon': str
            },
            ...
        ]
    }
    
    Query params:
    - limit: Max notifications to return (default 10)
    - include_read: Include read notifications (default false)
    """
    limit = int(request.GET.get('limit', 10))
    include_read = request.GET.get('include_read', 'false').lower() == 'true'
    
    # Get notifications
    if include_read:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:limit]
    else:
        notifications = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).order_by('-created_at')[:limit]
    
    # Get unread count
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Build response
    data = {
        'unread_count': unread_count,
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message[:100] + '...' if len(n.message) > 100 else n.message,
                'type': n.notification_type,
                'created_at': n.created_at.isoformat(),
                'action_url': n.action_url or None,
                'icon': get_notification_icon(n.notification_type),
                'is_read': n.is_read,
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)


@login_required
def get_unread_count_ajax(request):
    """
    Get count of unread notifications (AJAX endpoint).
    
    Returns:
    {'unread_count': int}
    
    Used for: Notification badge in header
    """
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': unread_count})


@login_required
@require_POST
def mark_notification_read_ajax(request, notification_id):
    """
    Mark notification as read (AJAX endpoint).
    
    Returns:
    {'success': bool, 'message': str}
    """
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )
        
        notification.mark_as_read()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def mark_all_notifications_read_ajax(request):
    """
    Mark all notifications as read for user (AJAX endpoint).
    
    Returns:
    {'success': bool, 'message': str, 'count': int}
    """
    try:
        unread = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        )
        
        count = unread.count()
        unread.update(is_read=True, read_at=timezone.now())
        
        return JsonResponse({
            'success': True,
            'message': f'Marked {count} notifications as read',
            'count': count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
@require_POST
def delete_notification_ajax(request, notification_id):
    """
    Delete a notification (AJAX endpoint).
    
    Returns:
    {'success': bool, 'message': str}
    """
    try:
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user
        )
        
        notification.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Notification deleted'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


# ============================================================================
# PARENT NOTIFICATIONS VIEW
# ============================================================================

@login_required
@require_parent
def parent_notifications_view(request):
    """
    Parent notifications dashboard - list all notifications.
    
    GET params:
    - type: Filter by notification type
    - unread: Show only unread (true/false)
    - page: Pagination
    
    Context:
    - notifications: Paginated list of notifications
    - unread_count: Count of unread notifications
    - types: Available notification types for filtering
    """
    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')
    
    # Filter by type
    notif_type = request.GET.get('type')
    if notif_type:
        notifications = notifications.filter(notification_type=notif_type)
    
    # Filter by read status
    unread_only = request.GET.get('unread', 'false').lower() == 'true'
    if unread_only:
        notifications = notifications.filter(is_read=False)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unread count
    unread_count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Get available types
    types = dict(Notification.NOTIFICATION_TYPES)
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'notification_types': types,
        'selected_type': notif_type,
        'unread_only': unread_only,
        'section': 'parent_notifications',
    }
    
    return render(request, 'parent/parent_notifications.html', context)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_notification_icon(notification_type):
    """Get Material Design 3 icon name for notification type"""
    icon_map = {
        'grade_posted': 'school',
        'payment_due': 'attach_money',
        'payment_overdue': 'warning',
        'attendance_alert': 'person_raise_hand',
        'assignment_due': 'assignment',
        'event_reminder': 'event',
        'schedule_change': 'schedule',
        'message': 'mail',
        'announcement': 'campaign',
        'admin_alert': 'admin_panel_settings',
        'system_alert': 'error',
        'other': 'notifications',
    }
    return icon_map.get(notification_type, 'notifications')


def get_notification_badge_color(notification_type):
    """Get Tailwind color class for notification badge"""
    color_map = {
        'grade_posted': 'bg-blue-100 text-blue-800',
        'payment_due': 'bg-orange-100 text-orange-800',
        'payment_overdue': 'bg-red-100 text-red-800',
        'attendance_alert': 'bg-yellow-100 text-yellow-800',
        'assignment_due': 'bg-purple-100 text-purple-800',
        'event_reminder': 'bg-green-100 text-green-800',
        'schedule_change': 'bg-indigo-100 text-indigo-800',
        'message': 'bg-cyan-100 text-cyan-800',
        'announcement': 'bg-pink-100 text-pink-800',
        'admin_alert': 'bg-gray-100 text-gray-800',
        'system_alert': 'bg-red-100 text-red-800',
        'other': 'bg-gray-100 text-gray-800',
    }
    return color_map.get(notification_type, 'bg-gray-100 text-gray-800')


def format_notification_time(created_at):
    """Format notification timestamp for display"""
    now = timezone.now()
    diff = now - created_at
    
    # Less than 1 minute
    if diff.total_seconds() < 60:
        return "just now"
    
    # Less than 1 hour
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    
    # Less than 1 day
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    
    # Less than 7 days
    elif diff.days < 7:
        return f"{diff.days}d ago"
    
    # Show date
    else:
        return created_at.strftime('%b %d')
