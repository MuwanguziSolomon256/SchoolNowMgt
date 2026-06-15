"""
Models for School Management System MVP.

IMPORTANT: Make sure to add the following to settings.py before running migrations:
    AUTH_USER_MODEL = 'SchoolNowMgt.CustomUser'

This custom user model is set in schoolmgmt_project/settings.py but must be
verified before generating any migrations.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    """Custom manager for the CustomUser model."""
    
    def create_user(self, username, email, password=None, school=None, **extra_fields):
        """Create and save a regular user."""
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        if not school:
            raise ValueError('School field is required')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, school=school, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, school=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, school=school, **extra_fields)


class School(models.Model):
    """Represents a school institution."""
    
    name = models.CharField(max_length=200)
    registration_number = models.CharField(max_length=100, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to='school_logos/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'School'
        verbose_name_plural = 'Schools'


class CustomUser(AbstractUser):
    """
    Custom user model extending AbstractUser.
    
    Supports multiple roles: admin, teacher, non-teaching staff, and parent.
    Each user must be associated with a school.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('non_teaching_staff', 'Non-Teaching Staff'),
        ('parent', 'Parent'),
    ]
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, db_index=True)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='users',
        db_index=True
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class StaffProfile(models.Model):
    """
    Extended profile for teaching and non-teaching staff.
    
    Links to CustomUser for staff members only (teachers and non-teaching staff).
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['teacher', 'non_teaching_staff']}
    )
    employee_id = models.CharField(max_length=50, unique=True)
    position = models.CharField(max_length=100)  # e.g., Class Teacher, Head Teacher, Cleaner
    qualification = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    date_joined = models.DateField()
    date_left = models.DateField(null=True, blank=True)
    is_full_time = models.BooleanField(default=True)
    
    # Emergency Contact Information
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Bank Account Details
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    account_holder_name = models.CharField(max_length=200, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} — {self.position}"
    
    class Meta:
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'


class ClassGrade(models.Model):
    """Represents a class/grade level within a school."""
    
    CURRICULUM_CHOICES = [
        ('national', 'Uganda National Curriculum'),
        ('international', 'International Curriculum'),
    ]
    
    name = models.CharField(max_length=50)
    level = models.IntegerField()  # 1-7 for P1-P7, 9-12 for international
    curriculum = models.CharField(
        max_length=20,
        choices=CURRICULUM_CHOICES,
        default='national',
        db_index=True
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes'
    )
    class_teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_assigned'
    )
    capacity = models.IntegerField(default=45)
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('name', 'school', 'curriculum')


class Subject(models.Model):
    """Represents a curriculum subject."""
    
    CURRICULUM_CHOICES = [
        ('national', 'Uganda National Curriculum'),
        ('international', 'International Curriculum'),
    ]
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10)
    curriculum = models.CharField(
        max_length=20,
        choices=CURRICULUM_CHOICES,
        default='national',
        db_index=True
    )
    
    def __str__(self):
        return f"{self.code} — {self.name}"
    
    class Meta:
        unique_together = ('name', 'code', 'curriculum')


class Student(models.Model):
    """Represents a student in the school."""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('graduated', 'Graduated'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    CURRICULUM_CHOICES = [
        ('national', 'Uganda National Curriculum'),
        ('international', 'International Curriculum'),
    ]
    
    admission_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    curriculum = models.CharField(
        max_length=20,
        choices=CURRICULUM_CHOICES,
        default='national',
        db_index=True
    )
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.PROTECT,
        related_name='students',
        db_index=True
    )
    parent_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'parent'}
    )
    parent_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=20)
    date_admitted = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    photo = models.ImageField(upload_to='students/', blank=True)
    
    def __str__(self):
        return f"{self.admission_number} — {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        ordering = ['class_grade', 'last_name']


class Grade(models.Model):
    """Represents a student's academic grade in a subject for a specific term and year."""
    
    TERM_CHOICES = [
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
    ]
    
    SEMESTER_CHOICES = [
        ('semester_1', 'Semester 1'),
        ('semester_2', 'Semester 2'),
    ]
    
    CURRICULUM_CHOICES = [
        ('national', 'Uganda National Curriculum'),
        ('international', 'International Curriculum'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='grades'
    )
    curriculum = models.CharField(
        max_length=20,
        choices=CURRICULUM_CHOICES,
        default='national',
        db_index=True
    )
    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES,
        blank=True,
        db_index=True,
        help_text="For Uganda National curriculum"
    )
    semester = models.CharField(
        max_length=10,
        choices=SEMESTER_CHOICES,
        blank=True,
        db_index=True,
        help_text="For International curriculum"
    )
    academic_year = models.CharField(
        max_length=4,
        db_index=True
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grades_recorded'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student} — {self.subject} — {self.term} {self.academic_year}: {self.score}"
    
    @property
    def letter_grade(self):
        """Compute letter grade from score."""
        if self.score >= 75:
            return 'A'
        elif self.score >= 65:
            return 'B'
        elif self.score >= 50:
            return 'C'
        elif self.score >= 40:
            return 'D'
        else:
            return 'F'
    
    class Meta:
        unique_together = ('student', 'subject', 'curriculum', 'term', 'semester', 'academic_year')
        ordering = ['-academic_year', 'term']


class Enquiry(models.Model):
    """
    Represents a parent enquiry about school enrollment.
    
    Public form submissions (no login required) to capture contact information
    and track the status of prospective student applications from inquiry through
    enrollment conversion.
    """
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('enrolled', 'Enrolled'),
        ('lost', 'Lost'),
    ]
    
    parent_name = models.CharField(max_length=200)
    parent_phone = models.CharField(max_length=20)
    child_name = models.CharField(max_length=200)
    interested_class = models.ForeignKey(
        ClassGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enquiries'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='enquiries'
    )
    enquiry_date = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    notes = models.TextField(blank=True)
    converted_student = models.OneToOneField(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_enquiry'
    )
    followed_up_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"Enquiry: {self.child_name} ({self.status})"
    
    class Meta:
        ordering = ['-enquiry_date']
        verbose_name_plural = 'Enquiries'


class StudentAttendance(models.Model):
    """
    Tracks daily attendance for students.
    
    Supports offline-first architecture: records marked offline have synced=False.
    Background sync job queries synced=False records and updates to True after sync.
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='student_attendance_marked'
    )
    synced = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} — {self.date} — {self.status}"
    
    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']


class StaffAttendance(models.Model):
    """
    Tracks daily attendance and time tracking for staff.
    
    Includes time_in/time_out for granular tracking and reason field for
    absences or late arrivals. Supports offline-first architecture via synced flag.
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='staff_attendance_marked'
    )
    synced = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.staff} — {self.date} — {self.status}"
    
    class Meta:
        unique_together = ('staff', 'date')
        ordering = ['-date']


class TeacherAttendance(models.Model):
    """
    Tracks daily attendance and time tracking for teachers.
    
    Similar to StaffAttendance, this tracks when teachers clock in/out,
    their daily status (present, absent, late), and any remarks.
    Also tracks break sessions and durations for comprehensive shift management.
    """
    
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='teacher_attendance_records',
        limit_choices_to={'user__role': 'teacher'}
    )
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)
    break_count = models.IntegerField(default=0, help_text="Number of breaks taken during the shift")
    total_break_duration = models.IntegerField(
        default=0,
        help_text="Total break duration in minutes"
    )
    reason = models.TextField(blank=True)
    marked_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='teacher_attendance_marked'
    )
    synced = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.staff} — {self.date} — {self.status}"
    
    def get_shift_duration(self):
        """
        Calculate total shift duration in minutes (including break time).
        Returns None if teacher is still clocked in or hasn't clocked in.
        """
        if not self.time_in or not self.time_out:
            return None
        
        from datetime import datetime, timedelta
        # Convert time objects to datetime for calculation
        time_in_dt = datetime.combine(self.date, self.time_in)
        time_out_dt = datetime.combine(self.date, self.time_out)
        
        # Handle case where time_out is next day
        if time_out_dt < time_in_dt:
            time_out_dt += timedelta(days=1)
        
        delta = time_out_dt - time_in_dt
        return int(delta.total_seconds() / 60)  # Return in minutes
    
    def get_shift_duration_excluding_breaks(self):
        """
        Calculate shift duration excluding break time in minutes.
        Returns None if teacher hasn't clocked out yet.
        """
        total_duration = self.get_shift_duration()
        if total_duration is None:
            return None
        return total_duration - self.total_break_duration
    
    def get_shift_hours(self):
        """
        Return shift duration as formatted string (e.g., "8h 30m").
        Includes break time in total.
        """
        duration = self.get_shift_duration()
        if duration is None:
            return "Not clocked out"
        
        hours = duration // 60
        minutes = duration % 60
        return f"{hours}h {minutes}m"
    
    def get_is_clocked_in(self):
        """Check if teacher is currently clocked in (has time_in but no time_out)."""
        return self.time_in is not None and self.time_out is None
    
    class Meta:
        unique_together = ('staff', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['staff', '-date']),
            models.Index(fields=['date']),
        ]


class StaffBill(models.Model):
    """
    Tracks financial information for staff members including salary, deductions, and outstanding balance.
    
    Records monthly/periodic salary, deductions, advances, and calculates outstanding balance.
    """
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
    ]
    
    staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='bills'
    )
    month = models.DateField(help_text="Month/date for this billing period")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total deductions (tax, loans, etc.)")
    advances = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Salary advances given")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def outstanding_balance(self):
        """Calculate outstanding balance."""
        net_amount = self.salary - self.deductions - self.advances
        return max(0, net_amount - self.amount_paid)
    
    def __str__(self):
        return f"{self.staff} — {self.month.strftime('%B %Y')} — {self.status}"
    
    class Meta:
        unique_together = ('staff', 'month')
        ordering = ['-month']
        verbose_name = 'Staff Bill'
        verbose_name_plural = 'Staff Bills'


class FeeStructure(models.Model):
    """
    Defines fee amounts for each class/grade per term and academic year.
    
    Stores the fee structure for tuition, meals, and other charges that vary
    by class level and term. Used as the basis for student fee calculations.
    """
    
    TERM_CHOICES = [
        ('term_1', 'Term 1'),
        ('term_2', 'Term 2'),
        ('term_3', 'Term 3'),
    ]
    
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    term = models.CharField(
        max_length=10,
        choices=TERM_CHOICES
    )
    academic_year = models.CharField(max_length=4)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fee amount in Uganda Shillings (UGX)"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g., 'Tuition only' or 'Tuition + lunch'"
    )
    
    def __str__(self):
        return f"{self.class_grade} — {self.term} {self.academic_year}: UGX {self.amount}"
    
    class Meta:
        unique_together = ('class_grade', 'term', 'academic_year')


class FeePayment(models.Model):
    """
    Records individual student fee payments with transaction details.
    
    Tracks amount paid, payment method, and staff member who received payment.
    The balance_after field is calculated and stored by the view/service layer
    at save time and is NOT auto-computed by this model.
    """
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mtn_mobile_money', 'MTN Mobile Money'),
        ('airtel_money', 'Airtel Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='fee_payments',
        db_index=True
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(db_index=True)
    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES
    )
    transaction_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="MTN/Airtel reference number or bank transfer reference"
    )
    received_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='fees_received'
    )
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Outstanding balance after this payment (calculated by service layer)"
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} — UGX {self.amount_paid} on {self.payment_date}"
    
    class Meta:
        ordering = ['-payment_date']


class Timetable(models.Model):
    """
    Represents a timetable entry for a lesson scheduled for a class.
    
    Each entry links a class grade, subject, and teacher to a specific time slot
    on a given day of the week. Prevents classroom double-booking via unique constraint
    and prevents teacher double-booking via clean() method validation.
    """
    
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
    ]
    
    CURRICULUM_CHOICES = [
        ('national', 'Uganda National Curriculum'),
        ('international', 'International Curriculum'),
    ]
    
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.CASCADE,
        related_name='timetable_entries'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='timetable_entries'
    )
    curriculum = models.CharField(
        max_length=20,
        choices=CURRICULUM_CHOICES,
        default='national',
        db_index=True
    )
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.PROTECT,
        related_name='timetable_entries',
        db_index=True
    )
    day_of_week = models.CharField(
        max_length=10,
        choices=DAY_CHOICES,
        db_index=True
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.class_grade} — {self.subject} — {self.day_of_week} {self.start_time}–{self.end_time}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        conflicts = Timetable.objects.filter(
            teacher=self.teacher,
            day_of_week=self.day_of_week,
            start_time=self.start_time
        ).exclude(pk=self.pk)
        if conflicts.exists():
            raise ValidationError("This teacher already has a lesson at this time.")
    
    class Meta:
        unique_together = ('class_grade', 'day_of_week', 'start_time')
        ordering = ['day_of_week', 'start_time']


class RetentionAlert(models.Model):
    """
    Tracks student risk alerts for early intervention.
    
    Identifies students at risk of dropping out based on attendance, grades,
    or fee default status. Alerts can be marked as resolved with notes on
    intervention taken.
    """
    
    REASON_TYPE_CHOICES = [
        ('high_absenteeism', 'High Absenteeism'),
        ('low_grades', 'Low Grades'),
        ('fee_default', 'Fee Default'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='retention_alerts'
    )
    reason_type = models.CharField(
        max_length=30,
        choices=REASON_TYPE_CHOICES
    )
    detail = models.TextField(
        help_text="Human-readable description, e.g. 'Absent 4 out of last 5 school days'"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    resolution_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Alert: {self.student} — {self.reason_type} ({self.severity})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['resolved']),
        ]


class SMSLog(models.Model):
    """
    Records all SMS communications sent through the school management system.
    
    Pure audit trail for SMS tracking. Logs phone number, message content, and
    delivery status. No send logic in this model; Africa's Talking API integration
    lives in sms_service.py. Supports SMS linked to students, staff, or alerts,
    or standalone SMS to external numbers.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    recipient_phone = models.CharField(max_length=20)
    message = models.TextField()
    related_student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs'
    )
    related_staff = models.ForeignKey(
        StaffProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs'
    )
    related_alert = models.ForeignKey(
        RetentionAlert,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sms_logs'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    provider_response = models.TextField(
        blank=True,
        help_text="Raw response from Africa's Talking API"
    )
    
    def __str__(self):
        return f"SMS to {self.recipient_phone} — {self.status} at {self.sent_at}"
    
    class Meta:
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
        ]


class TeacherTask(models.Model):
    """
    Represents a task assigned to or created by a teacher.
    
    Teachers can create their own tasks related to grading, lesson prep, etc.
    Tasks have priority levels and due dates for better organization.
    """
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_tasks'
    )
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teacher_tasks'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.title} — {self.teacher.user.get_full_name()} ({self.priority})"
    
    class Meta:
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['due_date']),
        ]


class ActivityLog(models.Model):
    """
    Tracks significant teacher activities in the system for audit and dashboard display.
    
    Records actions like quiz submissions by students, messages from principal,
    system backups, attendance marking, and grade entry. Used to populate
    the Recent Activity feed on the teacher dashboard.
    """
    
    ACTIVITY_TYPE_CHOICES = [
        ('quiz_submission', 'Quiz Submission'),
        ('message', 'Message'),
        ('system_backup', 'System Backup'),
        ('attendance_marked', 'Attendance Marked'),
        ('grade_entered', 'Grade Entered'),
        ('circular_sent', 'Circular Sent'),
        ('lesson_created', 'Lesson Created'),
        ('other', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('success', 'Success'),
    ]
    
    teacher = models.ForeignKey(
        StaffProfile,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_TYPE_CHOICES
    )
    description = models.TextField()
    related_student = models.ForeignKey(
        Student,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    icon_name = models.CharField(
        max_length=50,
        default='info',
        help_text="Material Symbols icon name"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='info'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def __str__(self):
        return f"{self.activity_type} — {self.teacher.user.get_full_name()} at {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', '-created_at']),
            models.Index(fields=['activity_type']),
        ]


# ============================================================================
# MESSAGE SYSTEM MODELS
# ============================================================================


class MessageTemplate(models.Model):
    """
    Pre-defined message templates for admins to quickly send standardized messages.
    
    Supports placeholders like {student_name}, {parent_name}, {class_name} that
    are replaced with actual values when messages are sent to recipients.
    """
    
    CATEGORY_CHOICES = [
        ('attendance', 'Attendance Alert'),
        ('academic', 'Academic Performance'),
        ('event', 'School Event'),
        ('general', 'General Announcement'),
        ('discipline', 'Discipline Notice'),
        ('fees', 'Fee Payment'),
    ]
    
    ROLE_CHOICES = [
        ('teacher', 'Teachers'),
        ('staff', 'Support Staff'),
        ('parent', 'Parents'),
        ('all', 'All'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name (e.g., 'Low Attendance Alert')")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    intended_for = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='all',
        help_text="Which role(s) this template is intended for"
    )
    body = models.TextField(
        help_text="Template body with optional placeholders: {student_name}, {parent_name}, {class_name}, {teacher_name}"
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='message_templates_created'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='message_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['school', 'is_active']),
            models.Index(fields=['category']),
        ]


class Message(models.Model):
    """
    In-app messages sent by admins/staff to stakeholders or by parents to staff.
    
    Supports immediate delivery and scheduled delivery (processed by background cron).
    Each message creates MessageRecipient entries for targeted users.
    
    sender_type distinguishes between admin-sent bulk messages and parent-sent direct messages.
    """
    
    SENDER_TYPE_CHOICES = [
        ('admin', 'Admin/Staff'),
        ('parent', 'Parent'),
        ('support_staff', 'Support Staff'),
        ('teacher', 'Teacher'),
    ]
    
    RECIPIENT_TYPE_CHOICES = [
        ('all_teachers', 'All Teachers'),
        ('all_staff', 'All Support Staff'),
        ('all_staff_combined', 'All Teachers & Support Staff'),
        ('all_parents', 'All Parents'),
        ('class_specific', 'Parents of Specific Class'),
        ('class_announcement', 'Class Announcement (Parents)'),
        ('individual_parent', 'Individual Parent'),
        ('specific_teacher', 'Specific Teacher'),
        ('individual', 'Individual User'),
        ('admin', 'School Admin'),
    ]
    
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages_sent'
    )
    sender_type = models.CharField(
        max_length=15,
        choices=SENDER_TYPE_CHOICES,
        default='admin',
        help_text="Whether message was sent by admin/staff, parent, support staff, or teacher"
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    subject = models.CharField(max_length=200)
    body = models.TextField()
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages_using_template'
    )
    recipient_type = models.CharField(
        max_length=50,
        choices=RECIPIENT_TYPE_CHOICES,
        help_text="Targeting strategy for message recipients"
    )
    # For class_specific and individual targeting
    target_class = models.ForeignKey(
        ClassGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Used when recipient_type='class_specific'"
    )
    target_user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages_targeted_to_user',
        help_text="Used when recipient_type='individual'"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="If set, message will be delivered at this time (processed by cron). If null, delivered immediately."
    )
    is_sent = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Marks when message has been processed and recipients assigned"
    )
    
    def __str__(self):
        return f"{self.subject} — {self.recipient_type} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['school', '-created_at']),
            models.Index(fields=['is_sent', 'scheduled_at']),
        ]


class MessageRecipient(models.Model):
    """
    Junction table linking Message → CustomUser for efficient recipient tracking.
    
    Each recipient record tracks whether they've read the message and when.
    """
    
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='recipients'
    )
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when recipient marked message as read. Null if unread."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def __str__(self):
        status = "read" if self.read_at else "unread"
        return f"{self.message.subject} → {self.recipient.email} ({status})"
    
    class Meta:
        unique_together = ('message', 'recipient')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['read_at']),
        ]


class Event(models.Model):
    """
    Represents a school event (holiday, exam, activity, etc.).
    
    Admins can create and manage school calendar events that are visible
    to all staff and students.
    """
    
    EVENT_TYPE_CHOICES = [
        ('holiday', 'Holiday'),
        ('exam', 'Examination'),
        ('activity', 'School Activity'),
        ('meeting', 'Staff Meeting'),
        ('other', 'Other Event'),
    ]
    
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='events',
        db_index=True
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='other',
        db_index=True
    )
    start_date = models.DateField()
    end_date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='events_created'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.start_date})"
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['school', 'start_date']),
            models.Index(fields=['event_type']),
        ]


class Assignment(models.Model):
    """
    Represents a coursework assignment assigned to a class by a teacher.
    
    Each assignment is tied to a specific class, subject, and teacher.
    Students' individual submissions and grades are tracked via StudentAssignment.
    """
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class_grade = models.ForeignKey(
        ClassGrade,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='assignments'
    )
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'teacher'},
        related_name='assignments_created'
    )
    due_date = models.DateField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} — {self.subject.name} ({self.class_grade.name})"
    
    class Meta:
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['class_grade', 'subject']),
            models.Index(fields=['due_date']),
            models.Index(fields=['created_by']),
        ]


class StudentAssignment(models.Model):
    """
    Tracks individual student submissions, grades, and feedback for assignments.
    
    Through table linking Student → Assignment with submission tracking,
    grading, and teacher feedback. Status is manually set by teachers based on
    submission state and due date comparison.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Submission'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Submitted Late'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='student_assignments'
    )
    submission_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the student submitted the assignment"
    )
    submission_text = models.TextField(
        blank=True,
        help_text="Student's assignment submission text or link to uploaded file"
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Grade out of 100 (if graded)"
    )
    feedback = models.TextField(
        blank=True,
        help_text="Teacher feedback on the assignment"
    )
    graded_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_graded'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.full_name} — {self.assignment.title} ({self.status})"
    
    @property
    def letter_grade(self):
        """Compute letter grade from score."""
        if self.grade is None:
            return None
        if self.grade >= 75:
            return 'A'
        elif self.grade >= 65:
            return 'B'
        elif self.grade >= 50:
            return 'C'
        elif self.grade >= 40:
            return 'D'
        else:
            return 'F'
    
    class Meta:
        unique_together = ('student', 'assignment')
        ordering = ['-assignment__due_date']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['created_at']),
        ]


class AdminProfile(models.Model):
    """
    Extended profile for admin users with additional information.
    
    One-to-one relationship with CustomUser for admin role users.
    """
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='admin_profile',
        limit_choices_to={'role': 'admin'}
    )
    bio = models.TextField(blank=True, help_text="Brief biography or professional summary")
    department = models.CharField(max_length=100, blank=True, help_text="E.g., Administration, Leadership")
    office_location = models.CharField(max_length=255, blank=True, help_text="Office location in school")
    availability_hours = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="E.g., 8:00 AM - 5:00 PM, Monday to Friday"
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Admin Profile: {self.user.get_full_name()}"
    
    def get_profile_image_url(self):
        """Return profile picture URL or default."""
        if self.user.profile_picture:
            return self.user.profile_picture.url
        return '/static/images/default-avatar.png'
    
    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'


class BreakSession(models.Model):
    """
    Tracks individual break sessions for teachers during a shift.
    
    Linked to TeacherAttendance, allows detailed tracking of when
    teachers take breaks and for how long.
    """
    
    teacher_attendance = models.ForeignKey(
        TeacherAttendance,
        on_delete=models.CASCADE,
        related_name='break_sessions',
        help_text="Link to the teacher's shift attendance record"
    )
    break_in_time = models.TimeField(
        help_text="Time when break started"
    )
    break_out_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time when break ended. Null if break is still active."
    )
    reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for break (e.g., lunch, restroom, personal)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.teacher_attendance.staff} — Break at {self.break_in_time}"
    
    def get_break_duration(self):
        """
        Calculate break duration in minutes.
        Returns None if break is still active (break_out_time is null).
        """
        if self.break_out_time is None:
            return None
        
        from datetime import datetime, timedelta
        break_in_dt = datetime.combine(self.teacher_attendance.date, self.break_in_time)
        break_out_dt = datetime.combine(self.teacher_attendance.date, self.break_out_time)
        
        # Handle case where break_out_time is on next day (unusual but possible for edge cases)
        if break_out_dt < break_in_dt:
            break_out_dt += timedelta(days=1)
        
        delta = break_out_dt - break_in_dt
        return int(delta.total_seconds() / 60)  # Return in minutes
    
    def get_is_active(self):
        """Check if this break session is currently active."""
        return self.break_out_time is None
    
    class Meta:
        ordering = ['teacher_attendance', 'break_in_time']
        indexes = [
            models.Index(fields=['teacher_attendance', '-break_in_time']),
        ]
        verbose_name = 'Break Session'
        verbose_name_plural = 'Break Sessions'
