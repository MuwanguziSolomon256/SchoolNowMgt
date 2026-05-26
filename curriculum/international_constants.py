"""
International Curriculum Constants and Grading Functions.

Defines curriculum structure, terms, grade bands, and grading thresholds
for Cambridge IGCSE and IB (Primary Years Programme / Middle Years Programme).
"""

# Semesters per year (international standard)
INTERNATIONAL_TERMS = [
    ('semester_1', 'Semester 1'),
    ('semester_2', 'Semester 2'),
]

# IGCSE Grade Bands (A*–U)
IGCSE_GRADE_BANDS = [
    ('A_STAR', 'A*'),
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
    ('E', 'E'),
    ('F', 'F'),
    ('G', 'G'),
    ('U', 'U — Ungraded'),
]

# IB Grade Bands (7–1)
IB_GRADE_BANDS = [
    ('7', '7 — Excellent'),
    ('6', '6 — Very good'),
    ('5', '5 — Good'),
    ('4', '4 — Satisfactory'),
    ('3', '3 — Mediocre'),
    ('2', '2 — Poor'),
    ('1', '1 — Very poor'),
]

# Score to IGCSE grade mapping (percentage → IGCSE grade)
IGCSE_SCORE_TO_GRADE = [
    (90, 'A_STAR'),
    (80, 'A'),
    (70, 'B'),
    (60, 'C'),
    (50, 'D'),
    (40, 'E'),
    (30, 'F'),
    (20, 'G'),
    (0,  'U'),
]

# Score to IB grade mapping (percentage → IB grade)
IB_SCORE_TO_GRADE = [
    (86, '7'),
    (71, '6'),
    (56, '5'),
    (41, '4'),
    (26, '3'),
    (11, '2'),
    (0,  '1'),
]


def percentage_to_igcse(score):
    """
    Convert numeric percentage score (0–100) to IGCSE grade band.
    
    Args:
        score (float): Numeric score from 0 to 100.
    
    Returns:
        str: IGCSE grade code (A_STAR, A, B, ..., U).
    
    Example:
        >>> percentage_to_igcse(85)
        'A'
        >>> percentage_to_igcse(55)
        'D'
        >>> percentage_to_igcse(15)
        'U'
    """
    for threshold, grade in IGCSE_SCORE_TO_GRADE:
        if score >= threshold:
            return grade
    return 'U'


def percentage_to_ib(score):
    """
    Convert numeric percentage score (0–100) to IB grade band (7–1).
    
    Args:
        score (float): Numeric score from 0 to 100.
    
    Returns:
        str: IB grade code (7, 6, 5, ..., 1).
    
    Example:
        >>> percentage_to_ib(75)
        '6'
        >>> percentage_to_ib(50)
        '5'
        >>> percentage_to_ib(10)
        '1'
    """
    for threshold, grade in IB_SCORE_TO_GRADE:
        if score >= threshold:
            return grade
    return '1'
