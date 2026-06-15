"""
Custom template filters for gradebook display and grade calculations.
"""

from django import template

register = template.Library()


@register.filter
def lookup(dict_obj, key):
    """
    Look up a value in a dictionary using a key.
    Usage: {{ dict|lookup:key }}
    """
    if isinstance(dict_obj, dict):
        return dict_obj.get(key)
    return None


@register.filter
def subject_scores(grades_dict):
    """
    Extract scores from grades dictionary for a student.
    Returns a list of scores for averaging.
    Usage: {{ grades_dict|subject_scores }}
    """
    if not isinstance(grades_dict, dict):
        return []
    
    scores = []
    for grade in grades_dict.values():
        if grade and hasattr(grade, 'score'):
            scores.append(float(grade.score))
    return scores


@register.filter
def average(scores_list):
    """
    Calculate average of a list of scores.
    Usage: {{ scores|average }}
    """
    if not scores_list or not isinstance(scores_list, list):
        return None
    
    if len(scores_list) == 0:
        return None
    
    return round(sum(scores_list) / len(scores_list), 2)


@register.filter
def widthratio(value, max_value, max_width):
    """
    Calculate width percentage for bar charts.
    Usage: style="width: {% widthratio count student_count 100 %}%"
    """
    try:
        if max_value == 0:
            return 0
        return int((float(value) / float(max_value)) * float(max_width))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
