"""
Uganda National Curriculum Constants and Grading Functions.

Defines curriculum structure, terms, subjects by level, and grading thresholds
for Uganda Ministry of Education and Sports (MoES) curriculum.
"""

# Terms per year
UGANDA_TERMS = [
    ('term_1', 'Term 1'),
    ('term_2', 'Term 2'),
    ('term_3', 'Term 3'),
]

# Subjects by primary level (P1–P7)
UGANDA_SUBJECTS_BY_LEVEL = {
    1: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Local Language',
        'Creative Arts',
        'PE',
    ],
    2: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Local Language',
        'Creative Arts',
        'PE',
    ],
    3: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Local Language',
        'Creative Arts',
        'PE',
    ],
    4: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Kiswahili',
        'Agriculture',
        'Creative Arts',
        'PE',
    ],
    5: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Kiswahili',
        'Agriculture',
        'Creative Arts',
        'PE',
    ],
    6: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Kiswahili',
        'Agriculture',
        'Creative Arts',
        'PE',
    ],
    7: [
        'English',
        'Mathematics',
        'Science',
        'Social Studies',
        'Religious Education',
        'Kiswahili',
        'Agriculture',
        'Creative Arts',
        'PE',
        'ICT',
    ],
}

# Letter grade thresholds (score → letter)
LETTER_GRADE_THRESHOLDS = [
    (75, 'A'),
    (65, 'B'),
    (50, 'C'),
    (40, 'D'),
    (0, 'F'),
]

# PLE (Primary Leaving Examination) division thresholds
# Aggregate points → division name
PLE_DIVISION_THRESHOLDS = [
    (4, '1st Division'),
    (13, '2nd Division'),
    (25, '3rd Division'),
    (33, '4th Division'),
    (37, 'Ungraded'),
]


def get_letter_grade(score):
    """
    Compute letter grade from numeric score (0–100).
    
    Args:
        score (float): Numeric score from 0 to 100.
    
    Returns:
        str: Letter grade (A, B, C, D, or F).
    
    Example:
        >>> get_letter_grade(78)
        'A'
        >>> get_letter_grade(55)
        'C'
    """
    if score is None:
        return 'F'
    
    for threshold, letter in LETTER_GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    
    return 'F'


def get_ple_division(aggregate_points):
    """
    Compute PLE division from aggregate points.
    
    Args:
        aggregate_points (int): Total aggregate points.
    
    Returns:
        str: Division name (1st Division–Ungraded).
    
    Example:
        >>> get_ple_division(8)
        '1st Division'
        >>> get_ple_division(30)
        '3rd Division'
    """
    if aggregate_points is None:
        return 'Ungraded'
    
    for max_points, division in PLE_DIVISION_THRESHOLDS:
        if aggregate_points <= max_points:
            return division
    
    return 'Ungraded'
