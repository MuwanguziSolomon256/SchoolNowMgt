from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    School, CustomUser, StaffProfile,
    ClassGrade, Subject, Student, Enquiry,
    StudentAttendance, StaffAttendance, TeacherAttendance, BreakSession,
    Grade, FeeStructure, FeePayment,
    Timetable, RetentionAlert, SMSLog,
)


# ============================================================================
# Custom Actions
# ============================================================================

def mark_as_contacted(modeladmin, request, queryset):
    queryset.update(status='contacted')
mark_as_contacted.short_description = "Mark selected enquiries as contacted"


def mark_resolved(modeladmin, request, queryset):
    queryset.update(
        resolved=True,
        resolved_at=timezone.now(),
        resolved_by=request.user,
    )
mark_resolved.short_description = "Mark selected alerts as resolved"


def requeue_failed(modeladmin, request, queryset):
    queryset.filter(status='failed').update(status='pending')
requeue_failed.short_description = "Re-queue failed messages as pending"


# ============================================================================
# Inline Classes
# ============================================================================

class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    fields = ['subject', 'term', 'academic_year', 'score',
              'letter_grade_display']
    readonly_fields = ['letter_grade_display']
    ordering = ['-academic_year', 'term']

    def letter_grade_display(self, obj):
        return obj.letter_grade
    letter_grade_display.short_description = 'Grade'


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    fields = ['student', 'amount_paid', 'payment_method',
              'transaction_id', 'balance_after', 'payment_date']
    readonly_fields = ['payment_date']


# ============================================================================
# 1. SchoolAdmin
# ============================================================================

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'registration_number', 'phone', 'email']
    search_fields = ['name', 'registration_number']


# ============================================================================
# 2. CustomUserAdmin
# ============================================================================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'get_user_full_name', 'role', 
                    'get_school_name', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = UserAdmin.fieldsets + (
        ('School Info', {
            'fields': ('role', 'school', 'phone', 'profile_picture')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('School Info', {
            'fields': ('role', 'school', 'phone')
        }),
    )
    
    def get_user_full_name(self, obj):
        """Safely get full name of user."""
        try:
            full_name = obj.get_full_name()
            return full_name if full_name.strip() else obj.username
        except Exception:
            return obj.username
    get_user_full_name.short_description = 'Full Name'
    
    def get_school_name(self, obj):
        """Safely get school name."""
        try:
            return obj.school.name if obj.school else '-'
        except Exception:
            return '-'
    get_school_name.short_description = 'School'


# ============================================================================
# 3. StaffProfileAdmin
# ============================================================================

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'position', 'is_full_time',
                    'date_joined', 'date_left']
    list_filter = ['position', 'is_full_time']
    search_fields = ['user__first_name', 'user__last_name', 'employee_id',
                     'position']
    raw_id_fields = ['user']


# ============================================================================
# 4. ClassGradeAdmin
# ============================================================================

@admin.register(ClassGrade)
class ClassGradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'school', 'class_teacher',
                    'capacity']
    list_filter = ['level', 'school']
    search_fields = ['name']


# ============================================================================
# 5. SubjectAdmin
# ============================================================================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['name', 'code']


# ============================================================================
# 6. StudentAdmin
# ============================================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'full_name', 'class_grade',
                    'status', 'parent_phone', 'date_admitted']
    list_filter = ['status', 'class_grade', 'gender']
    search_fields = ['admission_number', 'first_name', 'last_name',
                     'parent_name', 'parent_phone']
    readonly_fields = ['date_admitted']
    inlines = [GradeInline]

    fieldsets = (
        ('Personal Details', {
            'fields': ('admission_number', 'first_name', 'last_name',
                       'date_of_birth', 'gender', 'photo')
        }),
        ('Enrollment', {
            'fields': ('class_grade', 'status', 'date_admitted')
        }),
        ('Parent / Guardian', {
            'fields': ('parent_name', 'parent_phone', 'parent_user')
        }),
    )


# ============================================================================
# 7. EnquiryAdmin
# ============================================================================

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ['child_name', 'parent_name', 'parent_phone',
                    'interested_class', 'status', 'enquiry_date',
                    'followed_up_by']
    list_filter = ['status', 'interested_class']
    search_fields = ['child_name', 'parent_name', 'parent_phone']
    readonly_fields = ['enquiry_date', 'converted_student']
    actions = [mark_as_contacted]


# ============================================================================
# 8. StudentAttendanceAdmin
# ============================================================================

@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'marked_by', 'synced']
    list_filter = ['status', 'date', 'synced']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__admission_number']
    date_hierarchy = 'date'


# ============================================================================
# 9. StaffAttendanceAdmin
# ============================================================================

@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'status', 'time_in', 'time_out',
                    'synced']
    list_filter = ['status', 'date', 'synced']
    search_fields = ['staff__user__first_name', 'staff__user__last_name',
                     'staff__employee_id']
    date_hierarchy = 'date'


# ============================================================================
# 9b. BreakSessionInline
# ============================================================================

class BreakSessionInline(admin.TabularInline):
    model = BreakSession
    extra = 0
    fields = ['break_in_time', 'break_out_time', 'reason', 'get_duration_display']
    readonly_fields = ['get_duration_display', 'created_at', 'updated_at']
    ordering = ['break_in_time']
    
    def get_duration_display(self, obj):
        duration = obj.get_break_duration()
        if duration is None:
            return "Active" if obj.get_is_active() else "—"
        hours = duration // 60
        minutes = duration % 60
        return f"{hours}h {minutes}m"
    get_duration_display.short_description = "Duration"


# ============================================================================
# 9c. TeacherAttendanceAdmin
# ============================================================================

@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'status', 'time_in', 'time_out',
                    'break_count', 'total_break_duration_display', 'shift_duration_display']
    list_filter = ['status', 'date', 'staff__user__school']
    search_fields = ['staff__user__first_name', 'staff__user__last_name',
                     'staff__employee_id']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'shift_duration_display',
                       'shift_duration_excluding_breaks_display', 'break_count_info']
    inlines = [BreakSessionInline]
    
    fieldsets = (
        ('Teacher Information', {
            'fields': ('staff', 'date', 'status')
        }),
        ('Clock In/Out Times', {
            'fields': ('time_in', 'time_out')
        }),
        ('Break Information', {
            'fields': ('break_count', 'break_count_info', 'total_break_duration')
        }),
        ('Shift Duration Summary', {
            'fields': ('shift_duration_display', 'shift_duration_excluding_breaks_display')
        }),
        ('Additional Information', {
            'fields': ('reason', 'marked_by', 'synced')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_break_duration_display(self, obj):
        """Display break duration in human-readable format."""
        hours = obj.total_break_duration // 60
        minutes = obj.total_break_duration % 60
        return f"{hours}h {minutes}m" if hours > 0 or minutes > 0 else "—"
    total_break_duration_display.short_description = "Break Duration"
    
    def shift_duration_display(self, obj):
        """Display total shift duration (including breaks)."""
        return obj.get_shift_hours()
    shift_duration_display.short_description = "Total Shift Duration"
    
    def shift_duration_excluding_breaks_display(self, obj):
        """Display shift duration excluding breaks."""
        duration = obj.get_shift_duration_excluding_breaks()
        if duration is None:
            return "Not clocked out"
        hours = duration // 60
        minutes = duration % 60
        return f"{hours}h {minutes}m"
    shift_duration_excluding_breaks_display.short_description = "Shift Duration (Excl. Breaks)"
    
    def break_count_info(self, obj):
        """Display break count with additional info."""
        return f"{obj.break_count} break(s) taken"
    break_count_info.short_description = "Break Summary"


# ============================================================================
# 9d. BreakSessionAdmin
# ============================================================================

@admin.register(BreakSession)
class BreakSessionAdmin(admin.ModelAdmin):
    list_display = ['get_teacher_name', 'get_attendance_date', 'break_in_time', 
                    'break_out_time', 'get_duration_display', 'reason']
    list_filter = ['created_at', 'teacher_attendance__date', 'teacher_attendance__staff__user__school']
    search_fields = ['teacher_attendance__staff__user__first_name',
                     'teacher_attendance__staff__user__last_name',
                     'teacher_attendance__staff__employee_id']
    readonly_fields = ['created_at', 'updated_at', 'get_duration_display']
    ordering = ['-teacher_attendance__date', '-break_in_time']
    
    fieldsets = (
        ('Break Session Information', {
            'fields': ('teacher_attendance', 'break_in_time', 'break_out_time')
        }),
        ('Duration', {
            'fields': ('get_duration_display',)
        }),
        ('Notes', {
            'fields': ('reason',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_teacher_name(self, obj):
        """Display teacher name."""
        return obj.teacher_attendance.staff.user.get_full_name()
    get_teacher_name.short_description = 'Teacher'
    
    def get_attendance_date(self, obj):
        """Display attendance date."""
        return obj.teacher_attendance.date
    get_attendance_date.short_description = 'Date'
    
    def get_duration_display(self, obj):
        """Display break duration in human-readable format."""
        duration = obj.get_break_duration()
        if duration is None:
            return "Active" if obj.get_is_active() else "—"
        hours = duration // 60
        minutes = duration % 60
        return f"{hours}h {minutes}m" if hours > 0 or minutes > 0 else f"{minutes}m"
    get_duration_display.short_description = 'Duration'


# ============================================================================
# 10. GradeAdmin
# ============================================================================

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'academic_year',
                    'score', 'letter_grade_display', 'recorded_by']
    list_filter = ['term', 'academic_year', 'subject']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__admission_number']

    def letter_grade_display(self, obj):
        grade = obj.letter_grade
        colours = {
            'A': 'green', 'B': 'blue', 'C': 'orange',
            'D': 'goldenrod', 'F': 'red'
        }
        colour = colours.get(grade, 'black')
        return format_html(
            '<strong style="color:{}">{}</strong>', colour, grade
        )
    letter_grade_display.short_description = 'Grade'


# ============================================================================
# 11. FeeStructureAdmin & FeePaymentAdmin
# ============================================================================

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['class_grade', 'term', 'academic_year', 'amount',
                    'description']
    list_filter = ['term', 'academic_year', 'class_grade']
    inlines = [FeePaymentInline]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_structure', 'amount_paid',
                    'payment_method', 'transaction_id', 'balance_after',
                    'payment_date', 'received_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__admission_number', 'transaction_id']
    readonly_fields = ['payment_date']
    date_hierarchy = 'payment_date'


# ============================================================================
# 12. TimetableAdmin
# ============================================================================

@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ['class_grade', 'subject', 'teacher', 'day_of_week',
                    'start_time', 'end_time']
    list_filter = ['day_of_week', 'class_grade', 'teacher']
    search_fields = ['teacher__user__first_name',
                     'teacher__user__last_name', 'subject__name']
    ordering = ['day_of_week', 'start_time']


# ============================================================================
# 13. RetentionAlertAdmin
# ============================================================================

@admin.register(RetentionAlert)
class RetentionAlertAdmin(admin.ModelAdmin):
    list_display = ['student', 'reason_type', 'severity', 'resolved',
                    'created_at', 'resolved_at', 'resolved_by']
    list_filter = ['resolved', 'severity', 'reason_type']
    search_fields = ['student__first_name', 'student__last_name',
                     'student__admission_number']
    readonly_fields = ['created_at', 'resolved_at']
    actions = [mark_resolved]

    def get_queryset(self, request):
        # Show unresolved alerts first by default
        return super().get_queryset(request).order_by('resolved',
                                                      '-created_at')


# ============================================================================
# 14. SMSLogAdmin
# ============================================================================

@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ['recipient_phone', 'related_student', 'status',
                    'sent_at', 'message_preview']
    list_filter = ['status', 'sent_at']
    search_fields = ['recipient_phone', 'related_student__first_name',
                     'related_student__last_name']
    readonly_fields = ['recipient_phone', 'message', 'related_student',
                       'related_staff', 'related_alert', 'sent_at',
                       'provider_response']
    actions = [requeue_failed]

    def message_preview(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 \
               else obj.message
    message_preview.short_description = 'Message'

    def has_add_permission(self, request):
        # SMS logs are created only by the system, never manually
        return False
