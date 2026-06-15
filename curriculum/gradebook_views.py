"""
Gradebook management views for both Uganda national and international curricula.

Provides teacher-facing gradebook views: list view, detail view, reporting, transcripts, and exports.
All views require teacher login and filter data by assigned classes and curriculum.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Count, F, Case, When, DecimalField
from django.http import HttpResponse, JsonResponse
import csv
from decimal import Decimal
from datetime import datetime

from SchoolNowMgt.models import (
    StaffProfile, ClassGrade, Grade, Student, Subject, Timetable
)
from .uganda_constants import UGANDA_TERMS, LETTER_GRADE_THRESHOLDS
from .international_constants import IGCSE_SCORE_TO_GRADE, IB_SCORE_TO_GRADE


def get_teacher_classes(teacher):
    """
    Fetch all ClassGrade objects where this teacher is the class_teacher.
    Returns queryset of ClassGrade ordered by curriculum then name.
    """
    return ClassGrade.objects.filter(
        class_teacher=teacher
    ).order_by('curriculum', 'name')


def get_class_students(class_grade):
    """
    Fetch all active students in a given ClassGrade, matching the class's curriculum.
    Returns queryset of Student ordered by last_name.
    """
    return Student.objects.filter(
        class_grade=class_grade,
        curriculum=class_grade.curriculum,
        status='active'
    ).order_by('last_name', 'first_name')


def get_class_subjects(class_grade):
    """
    Fetch all subjects taught in a given ClassGrade (via Timetable).
    Filters by curriculum and returns distinct subjects.
    """
    return Subject.objects.filter(
        timetable_entries__class_grade=class_grade,
        timetable_entries__curriculum=class_grade.curriculum,
        curriculum=class_grade.curriculum
    ).distinct().order_by('name')


def get_period_label(curriculum, term=None, semester=None, academic_year=None):
    """
    Generate a human-readable label for a term/semester and academic year.
    E.g., "Term 1, 2024" or "Semester 1, 2024"
    """
    if curriculum == 'national':
        if term:
            term_dict = {choice[0]: choice[1] for choice in UGANDA_TERMS}
            term_name = term_dict.get(term, term)
            return f"{term_name}, {academic_year}" if academic_year else term_name
    elif curriculum == 'international':
        if semester:
            semester_dict = {'semester_1': 'Semester 1', 'semester_2': 'Semester 2'}
            semester_name = semester_dict.get(semester, semester)
            return f"{semester_name}, {academic_year}" if academic_year else semester_name
    return academic_year or ''


@login_required
def gradebook_list(request):
    """
    List view: Display all students in a class with their grades in a grid format.
    
    GET params:
        - class_id: Required. ClassGrade ID to display.
        - term: Optional. Filter by term (national curriculum).
        - semester: Optional. Filter by semester (international curriculum).
        - academic_year: Optional. Filter by academic year. Defaults to current year.
    
    Context:
        - class_grade: The selected ClassGrade
        - students: List of active students in the class
        - subjects: List of subjects taught in the class
        - grades_dict: Nested dict {student_id: {subject_id: Grade or None}}
        - term/semester_choices: Available terms/semesters for filtering
        - selected_period: Currently selected term/semester
        - academic_year: Currently selected academic year
        - curriculum_type: Human-readable curriculum name
    """
    # Get teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get selected class (must be taught by this teacher)
    class_id = request.GET.get('class_id')
    if not class_id:
        # Show class selector
        teacher_classes = get_teacher_classes(staff)
        return render(request, 'teacher/gradebook_select_class.html', {
            'classes': teacher_classes,
        })
    
    class_grade = get_object_or_404(
        ClassGrade,
        id=class_id,
        class_teacher=staff
    )
    
    # Get students and subjects
    students = get_class_students(class_grade)
    subjects = get_class_subjects(class_grade)
    
    # Get filter parameters
    academic_year = request.GET.get('academic_year', str(datetime.now().year))
    term = request.GET.get('term', '')
    semester = request.GET.get('semester', '')
    
    # Build grade query filter based on curriculum
    grade_filter = Q(
        student__in=students,
        subject__in=subjects,
        curriculum=class_grade.curriculum,
        academic_year=academic_year
    )
    
    if class_grade.curriculum == 'national' and term:
        grade_filter &= Q(term=term)
    elif class_grade.curriculum == 'international' and semester:
        grade_filter &= Q(semester=semester)
    
    grades = Grade.objects.filter(grade_filter).select_related('student', 'subject')
    
    # Build nested dict: {student_id: {subject_id: Grade}}
    grades_dict = {}
    for student in students:
        grades_dict[student.id] = {}
        for subject in subjects:
            grades_dict[student.id][subject.id] = None
    
    for grade in grades:
        if grade.student.id in grades_dict and grade.subject.id in grades_dict[grade.student.id]:
            grades_dict[grade.student.id][grade.subject.id] = grade
    
    # Build student_grades list for easier template iteration
    student_grades = []
    for student in students:
        student_data = {
            'student': student,
            'grades': [],
            'subjects_scores': []
        }
        for subject in subjects:
            grade = grades_dict[student.id].get(subject.id)
            student_data['grades'].append({
                'subject': subject,
                'grade': grade,
                'score': grade.score if grade else None,
                'letter_grade': grade.letter_grade if grade else None,
                'remarks': grade.remarks if grade else None,
            })
            if grade and grade.score:
                student_data['subjects_scores'].append(float(grade.score))
        
        # Calculate average
        if student_data['subjects_scores']:
            student_data['average'] = round(sum(student_data['subjects_scores']) / len(student_data['subjects_scores']), 2)
        else:
            student_data['average'] = None
        
        student_grades.append(student_data)
    
    # Prepare period choices based on curriculum
    if class_grade.curriculum == 'national':
        period_choices = UGANDA_TERMS
        selected_period = term
        period_param = 'term'
    else:
        period_choices = [('semester_1', 'Semester 1'), ('semester_2', 'Semester 2')]
        selected_period = semester
        period_param = 'semester'
    
    curriculum_type = 'Uganda National Curriculum' if class_grade.curriculum == 'national' else 'International Curriculum'
    
    context = {
        'class_grade': class_grade,
        'students': students,
        'subjects': subjects,
        'grades_dict': grades_dict,
        'student_grades': student_grades,
        'period_choices': period_choices,
        'selected_period': selected_period,
        'period_param': period_param,
        'academic_year': academic_year,
        'current_year': datetime.now().year,
        'curriculum_type': curriculum_type,
    }
    
    return render(request, 'teacher/gradebook.html', context)


@login_required
def gradebook_detail(request, student_id):
    """
    Detail view: Display a single student's full gradebook (all terms/years).
    
    Path params:
        - student_id: Student ID to display.
    
    Context:
        - student: The Student object
        - grades_by_year_term: List of dicts {year, term, subjects_grades: []}
        - average_by_subject: Dict {subject_name: average_score}
        - overall_average: Overall average across all subjects/terms
        - curriculum_type: Human-readable curriculum name
    """
    # Get teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get student (must be in one of teacher's classes)
    student = get_object_or_404(
        Student,
        id=student_id,
        class_grade__class_teacher=staff
    )
    
    # Fetch all grades for this student
    all_grades = Grade.objects.filter(
        student=student,
        curriculum=student.curriculum
    ).select_related('subject').order_by('-academic_year', 'term', 'semester', 'subject__name')
    
    # Group by (academic_year, term/semester) for display
    grades_by_period = {}
    for grade in all_grades:
        year = grade.academic_year
        if student.curriculum == 'national':
            period = grade.term
        else:
            period = grade.semester
        
        key = (year, period)
        if key not in grades_by_period:
            grades_by_period[key] = []
        grades_by_period[key].append(grade)
    
    # Calculate subject averages
    subject_averages = {}
    for grade in all_grades:
        subject_name = grade.subject.name
        if subject_name not in subject_averages:
            subject_averages[subject_name] = []
        subject_averages[subject_name].append(float(grade.score))
    
    for subject_name in subject_averages:
        scores = subject_averages[subject_name]
        subject_averages[subject_name] = sum(scores) / len(scores) if scores else 0
    
    # Calculate overall average
    all_scores = [float(g.score) for g in all_grades]
    overall_average = sum(all_scores) / len(all_scores) if all_scores else 0
    
    curriculum_type = 'Uganda National Curriculum' if student.curriculum == 'national' else 'International Curriculum'
    
    context = {
        'student': student,
        'grades_by_period': grades_by_period,
        'subject_averages': subject_averages,
        'overall_average': round(overall_average, 2),
        'curriculum_type': curriculum_type,
    }
    
    return render(request, 'teacher/gradebook_detail.html', context)


@login_required
def grade_report(request):
    """
    Reporting view: Display class analytics and performance metrics.
    
    GET params:
        - class_id: Required. ClassGrade ID to report on.
        - term: Optional. For national curriculum.
        - semester: Optional. For international curriculum.
        - academic_year: Optional. Defaults to current year.
    
    Context:
        - class_grade: The selected ClassGrade
        - subject_averages: Dict {subject_name: average_score}
        - student_count: Total students in class
        - top_students: Top 3 students by average
        - bottom_students: Bottom 3 students by average
        - grade_distribution: Dict {grade_band: count}
        - curriculum_type: Human-readable curriculum name
    """
    # Get teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get selected class
    class_id = request.GET.get('class_id')
    if not class_id:
        teacher_classes = get_teacher_classes(staff)
        return render(request, 'teacher/report_select_class.html', {
            'classes': teacher_classes,
        })
    
    class_grade = get_object_or_404(
        ClassGrade,
        id=class_id,
        class_teacher=staff
    )
    
    # Get filter parameters
    academic_year = request.GET.get('academic_year', str(datetime.now().year))
    term = request.GET.get('term', '')
    semester = request.GET.get('semester', '')
    
    # Get students and subjects
    students = get_class_students(class_grade)
    subjects = get_class_subjects(class_grade)
    
    # Build grade query
    grade_filter = Q(
        student__in=students,
        subject__in=subjects,
        curriculum=class_grade.curriculum,
        academic_year=academic_year
    )
    
    if class_grade.curriculum == 'national' and term:
        grade_filter &= Q(term=term)
    elif class_grade.curriculum == 'international' and semester:
        grade_filter &= Q(semester=semester)
    
    grades = Grade.objects.filter(grade_filter).select_related('student', 'subject')
    
    # Calculate subject averages
    subject_averages = {}
    for subject in subjects:
        subject_grades = [g for g in grades if g.subject == subject]
        if subject_grades:
            avg = sum(float(g.score) for g in subject_grades) / len(subject_grades)
            subject_averages[subject.name] = round(avg, 2)
    
    # Calculate student averages for top/bottom ranking
    student_averages = {}
    for student in students:
        student_grades = [g for g in grades if g.student == student]
        if student_grades:
            avg = sum(float(g.score) for g in student_grades) / len(student_grades)
            student_averages[student] = round(avg, 2)
    
    # Top 3 and bottom 3 students
    sorted_students = sorted(student_averages.items(), key=lambda x: x[1], reverse=True)
    top_students = sorted_students[:3]
    bottom_students = sorted_students[-3:] if len(sorted_students) > 3 else []
    
    # Grade distribution (A, B, C, D, F for national; A*, A, B, etc. for international)
    grade_distribution = {}
    for grade in grades:
        if class_grade.curriculum == 'national':
            # Use letter grade property
            letter = grade.letter_grade
        else:
            # Use IGCSE or IB conversion
            if semester:
                # Assume IGCSE for now (can add logic to detect curriculum type)
                for threshold, grade_band in IGCSE_SCORE_TO_GRADE:
                    if float(grade.score) >= threshold:
                        letter = grade_band
                        break
                else:
                    letter = 'U'
            else:
                letter = '?'
        
        grade_distribution[letter] = grade_distribution.get(letter, 0) + 1
    
    curriculum_type = 'Uganda National Curriculum' if class_grade.curriculum == 'national' else 'International Curriculum'
    
    context = {
        'class_grade': class_grade,
        'subject_averages': subject_averages,
        'student_count': students.count(),
        'top_students': top_students,
        'bottom_students': bottom_students,
        'grade_distribution': grade_distribution,
        'curriculum_type': curriculum_type,
        'academic_year': academic_year,
    }
    
    return render(request, 'teacher/grade_report.html', context)


@login_required
def student_transcript(request, student_id):
    """
    Transcript view: Generate printable student transcript with all grades.
    
    Path params:
        - student_id: Student ID to generate transcript for.
    
    Context:
        - student: The Student object
        - school: The School object
        - grades_by_period: Grouped grades for display
        - overall_average: Overall average across all subjects
        - curriculum_type: Human-readable curriculum name
    """
    # Get teacher's StaffProfile (verify authorization)
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get student
    student = get_object_or_404(
        Student,
        id=student_id,
        class_grade__class_teacher=staff
    )
    
    # Fetch all grades
    all_grades = Grade.objects.filter(
        student=student,
        curriculum=student.curriculum
    ).select_related('subject').order_by('-academic_year', 'term', 'semester')
    
    # Group by period
    grades_by_period = {}
    for grade in all_grades:
        year = grade.academic_year
        period = grade.term or grade.semester
        key = (year, period)
        if key not in grades_by_period:
            grades_by_period[key] = []
        grades_by_period[key].append(grade)
    
    # Calculate overall average
    all_scores = [float(g.score) for g in all_grades]
    overall_average = sum(all_scores) / len(all_scores) if all_scores else 0
    
    curriculum_type = 'Uganda National Curriculum' if student.curriculum == 'national' else 'International Curriculum'
    school = student.class_grade.school
    
    context = {
        'student': student,
        'school': school,
        'grades_by_period': grades_by_period,
        'overall_average': round(overall_average, 2),
        'curriculum_type': curriculum_type,
        'generated_date': datetime.now().strftime('%d %B %Y'),
    }
    
    return render(request, 'teacher/student_transcript.html', context)


@login_required
def export_grades(request):
    """
    Export gradebook to CSV format.
    
    GET params:
        - class_id: Required. ClassGrade ID to export.
        - term: Optional. For national curriculum.
        - semester: Optional. For international curriculum.
        - academic_year: Optional. Defaults to current year.
        - format: Export format (csv default).
    
    Returns:
        CSV file download with headers: Student Name, Admission #, Subject1, Subject2, ..., Average
    """
    # Get teacher's StaffProfile
    staff = get_object_or_404(StaffProfile, user=request.user)
    
    # Get class
    class_id = request.GET.get('class_id')
    class_grade = get_object_or_404(
        ClassGrade,
        id=class_id,
        class_teacher=staff
    )
    
    # Get filter parameters
    academic_year = request.GET.get('academic_year', str(datetime.now().year))
    term = request.GET.get('term', '')
    semester = request.GET.get('semester', '')
    
    # Get students and subjects
    students = get_class_students(class_grade)
    subjects = get_class_subjects(class_grade)
    
    # Build grade query
    grade_filter = Q(
        student__in=students,
        subject__in=subjects,
        curriculum=class_grade.curriculum,
        academic_year=academic_year
    )
    
    if class_grade.curriculum == 'national' and term:
        grade_filter &= Q(term=term)
    elif class_grade.curriculum == 'international' and semester:
        grade_filter &= Q(semester=semester)
    
    grades = Grade.objects.filter(grade_filter).select_related('student', 'subject')
    
    # Build nested dict
    grades_dict = {}
    for student in students:
        grades_dict[student.id] = {}
        for subject in subjects:
            grades_dict[student.id][subject.id] = None
    
    for grade in grades:
        if grade.student.id in grades_dict:
            grades_dict[grade.student.id][grade.subject.id] = grade
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="gradebook_{class_grade.name}_{academic_year}.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    header = ['Student Name', 'Admission Number']
    for subject in subjects:
        header.append(subject.name)
    header.append('Average')
    writer.writerow(header)
    
    # Write student rows
    for student in students:
        row = [student.full_name, student.admission_number]
        scores = []
        
        for subject in subjects:
            grade = grades_dict[student.id][subject.id]
            if grade:
                row.append(float(grade.score))
                scores.append(float(grade.score))
            else:
                row.append('-')
        
        # Calculate average
        if scores:
            average = sum(scores) / len(scores)
            row.append(f"{average:.2f}")
        else:
            row.append('-')
        
        writer.writerow(row)
    
    return response
