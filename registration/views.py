# Re-export register_teacher from SchoolNowMgt.registration for consistency
from SchoolNowMgt.registration.views import register_teacher

__all__ = ['register_teacher']
