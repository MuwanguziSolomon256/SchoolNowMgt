"""
Parent Dashboard Views - Multi-school parent interface
Parents access multiple schools via StudentParentRelationship model
"""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone

from SchoolNowMgt.models import (
    CustomUser, StudentParentRelationship, Student, Grade, 
    StudentAttendance, FeePayment, FeeStructure, ClassGrade, Message,
)
from SchoolNowMgt.decorators import get_user_school


# ============================================================================
# Parent Decorators & Helpers
# ============================================================================

def require_parent(view_func):
    """Decorator: Verify user is a parent"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'parent':
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_parent_schools(parent):
    """Get list of schools where parent has students"""
    return StudentParentRelationship.objects.filter(
        parent=parent,
        is_active=True
    ).values_list('school', flat=True).distinct()


def get_parent_children(parent, school=None):
    """Get children for this parent (optionally filtered by school)"""
    query = StudentParentRelationship.objects.filter(
        parent=parent,
        is_active=True
    )
    if school:
        query = query.filter(school=school)
    return Student.objects.filter(
        id__in=query.values_list('student_id', flat=True)
    )


# ============================================================================
# 1. Parent Dashboard
# ============================================================================

@login_required
@require_parent
def parent_dashboard(request):
    """Main parent dashboard - overview of all children and schools"""
    parent = request.user
    
    # Get all parent relationships with schools
    relationships = StudentParentRelationship.objects.filter(
        parent=parent,
        is_active=True
    ).select_related('student', 'school').order_by('-is_primary_guardian', 'student__first_name')
    
    # Get statistics
    schools = get_parent_schools(parent)
    total_children = relationships.count()
    
    # Get recent academic performance (latest grades)
    recent_grades = Grade.objects.filter(
        student__in=get_parent_children(parent)
    ).order_by('-academic_year', '-term')[:5]
    
    # Get attendance summary for each child
    attendance_data = {}
    for student in get_parent_children(parent):
        total = StudentAttendance.objects.filter(student=student).count()
        present = StudentAttendance.objects.filter(
            student=student,
            attendance_status='present'
        ).count()
        attendance_data[student.id] = {
            'present': present,
            'total': total,
            'percentage': (present / total * 100) if total > 0 else 0
        }
    
    # Get outstanding fees
    outstanding_fees = FeePayment.objects.filter(
        student__in=get_parent_children(parent),
        balance_after__gt=0
    ).select_related('student', 'fee_structure').order_by('-payment_date')[:5]
    
    # Get unread messages
    unread_messages = Message.objects.filter(
        recipient=parent,
        is_read=False
    ).count()
    
    context = {
        'parent': parent,
        'relationships': relationships,
        'total_children': total_children,
        'schools_count': schools.count(),
        'recent_grades': recent_grades,
        'attendance_data': attendance_data,
        'outstanding_fees': outstanding_fees,
        'unread_messages': unread_messages,
    }
    
    return render(request, 'parent/parent_dashboard.html', context)


# ============================================================================
# 2. Parent Messages - Inbox
# ============================================================================

@login_required
@require_parent
def parent_message_inbox(request):
    """Parent message inbox with pagination"""
    parent = request.user
    
    # Get all messages for parent
    messages = Message.objects.filter(
        recipient=parent
    ).order_by('-created_at')
    
    # Paginate
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page', 1)
    messages_page = paginator.get_page(page_number)
    
    # Unread count
    unread_count = Message.objects.filter(
        recipient=parent,
        is_read=False
    ).count()
    
    context = {
        'messages': messages_page,
        'unread_count': unread_count,
        'total_messages': messages.count(),
    }
    
    return render(request, 'parent/parent_message_inbox.html', context)


# ============================================================================
# 3. Parent Message - Detail View
# ============================================================================

@login_required
@require_parent
def parent_message_detail(request, message_id):
    """View single message - mark as read"""
    parent = request.user
    message = get_object_or_404(Message, id=message_id, recipient=parent)
    
    # Mark as read if not already
    if not message.is_read:
        message.is_read = True
        message.is_read_at = timezone.now()
        message.save()
    
    # Get related messages (thread)
    related_messages = Message.objects.filter(
        Q(sender=message.sender, recipient=parent) |
        Q(sender=parent, recipient=message.sender)
    ).order_by('-created_at')[:20]
    
    context = {
        'message': message,
        'related_messages': related_messages,
    }
    
    return render(request, 'parent/parent_message_detail.html', context)


# ============================================================================
# 4. AJAX: Send Message
# ============================================================================

@login_required
@require_parent
@require_http_methods(["POST"])
@csrf_exempt
def parent_send_message_ajax(request):
    """AJAX endpoint to send message from parent"""
    try:
        data = json.loads(request.body)
        recipient_id = data.get('recipient_id')
        subject = data.get('subject', '')
        content = data.get('content', '')
        
        if not recipient_id or not content:
            return JsonResponse({
                'success': False,
                'error': 'Recipient and content required'
            }, status=400)
        
        recipient = get_object_or_404(CustomUser, id=recipient_id)
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            content=content,
            message_type='parent_to_staff'
        )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'created_at': message.created_at.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# 5. AJAX: Mark Message as Read
# ============================================================================

@login_required
@require_parent
@require_http_methods(["POST"])
@csrf_exempt
def parent_mark_message_read_ajax(request, message_id):
    """AJAX endpoint to mark message as read"""
    try:
        parent = request.user
        message = get_object_or_404(Message, id=message_id, recipient=parent)
        
        message.is_read = True
        message.is_read_at = timezone.now()
        message.save()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================================
# 6. AJAX: Get Unread Message Count
# ============================================================================

@login_required
@require_parent
def get_parent_unread_count_ajax(request):
    """AJAX endpoint to get unread message count"""
    parent = request.user
    unread_count = Message.objects.filter(
        recipient=parent,
        is_read=False
    ).count()
    
    return JsonResponse({
        'unread_count': unread_count
    })


# ============================================================================
# 7. Parent Children Dashboard
# ============================================================================

@login_required
@require_parent
def parent_children_dashboard(request):
    """View all children with detailed information"""
    parent = request.user
    
    # Get all parent relationships
    relationships = StudentParentRelationship.objects.filter(
        parent=parent,
        is_active=True
    ).select_related('student', 'school')
    
    print(f"\n=== DEBUG parent_children_dashboard ===")
    print(f"Parent: {parent} (ID={parent.id}, school={parent.school})")
    print(f"Relationships found: {relationships.count()}")
    
    children_data = []
    for rel in relationships:
        student = rel.student
        
        # Get current class
        current_class = student.class_grade
        
        # Get attendance percentage
        total_attendance = StudentAttendance.objects.filter(student=student).count()
        present_count = StudentAttendance.objects.filter(
            student=student,
            attendance_status='present'
        ).count()
        attendance_pct = (present_count / total_attendance * 100) if total_attendance > 0 else 0
        
        # Get latest grade
        latest_grade = Grade.objects.filter(student=student).order_by('-academic_year', '-term').first()
        
        # Get fee balance
        fee_balance = FeePayment.objects.filter(student=student).aggregate(
            total_balance=Sum('balance_after')
        )['total_balance'] or 0
        
        children_data.append({
            'student': student,
            'relationship': rel,
            'school': rel.school,
            'current_class': current_class,
            'attendance_percentage': attendance_pct,
            'latest_grade': latest_grade,
            'fee_balance': fee_balance,
        })
    
    # Paginate
    paginator = Paginator(children_data, 10)
    page_number = request.GET.get('page', 1)
    children_page = paginator.get_page(page_number)
    
    context = {
        'children': children_page,
        'total_children': len(children_data),
    }
    
    return render(request, 'parent/parent_children_dashboard.html', context)


# ============================================================================
# 8. Parent Academics Dashboard
# ============================================================================

@login_required
@require_parent
def parent_academics_dashboard(request):
    """View academic performance of all children"""
    parent = request.user
    
    children = get_parent_children(parent)
    
    # Get academic data for each child
    academic_data = []
    for student in children:
        # Get all grades for this student
        grades = Grade.objects.filter(student=student).order_by('-academic_year', '-term')
        
        # Get current class
        current_class = student.class_grade
        
        # Calculate GPA if available
        if grades:
            avg_score = grades.aggregate(
                avg=Avg('score')
            )['avg'] or 0
        else:
            avg_score = 0
        
        academic_data.append({
            'student': student,
            'current_class': current_class,
            'grades': grades,
            'average_score': avg_score,
            'total_subjects': grades.values('subject').distinct().count(),
        })
    
    context = {
        'academic_data': academic_data,
    }
    
    return render(request, 'parent/parent_academics_dashboard.html', context)


# ============================================================================
# 9. Parent Payments Dashboard
# ============================================================================

@login_required
@require_parent
def parent_payments_dashboard(request):
    """View fee payments and balances for all children"""
    parent = request.user
    
    children = get_parent_children(parent)
    
    # Get payment data for each child
    payment_data = []
    total_outstanding = 0
    
    for student in children:
        payments = FeePayment.objects.filter(
            student=student
        ).select_related('fee_structure').order_by('-payment_date')
        
        # Calculate totals
        total_paid = sum([p.amount_paid for p in payments])
        total_balance = sum([p.balance_after for p in payments])
        
        total_outstanding += total_balance
        
        # Get current fee structure
        current_fee = FeeStructure.objects.filter(
            class_grade=student.class_grade
        ).first()
        
        payment_data.append({
            'student': student,
            'payments': payments,
            'total_paid': total_paid,
            'total_balance': total_balance,
            'current_fee': current_fee,
        })
    
    # Paginate
    paginator = Paginator(payment_data, 10)
    page_number = request.GET.get('page', 1)
    payments_page = paginator.get_page(page_number)
    
    context = {
        'payment_data': payments_page,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'parent/parent_payments_dashboard.html', context)
