from datetime import date
from SchoolNowMgt.models import StaffProfile


def generate_employee_id(school):
    """
    Generate a unique employee ID for a teacher at a school.
    
    Format: PREFIX-YY-XXXX
    - PREFIX: First 4 characters of school registration_number (uppercase, spaces/hyphens stripped)
    - YY: Current year (last 2 digits)
    - XXXX: Sequential number (zero-padded to 4 digits)
    
    Includes collision avoidance: if the generated ID already exists, increments
    the sequence number and retries until a unique ID is found.
    
    Args:
        school: School instance
    
    Returns:
        str: Unique employee ID in format "PREFIX-YY-XXXX"
    """
    # Extract and clean the prefix from registration_number
    reg_number = school.registration_number.strip()
    prefix = reg_number[:4].upper().replace(' ', '').replace('-', '')
    
    # Get current year as 2-digit string
    current_year = str(date.today().year)[-2:]
    
    # Count existing StaffProfile records for this school and add 1
    school_staff_count = StaffProfile.objects.filter(user__school=school).count()
    sequence = school_staff_count + 1
    
    # Try to generate a unique ID with collision avoidance
    max_attempts = 1000  # Prevent infinite loop
    attempt = 0
    
    while attempt < max_attempts:
        seq_str = str(sequence).zfill(4)
        employee_id = f"{prefix}-{current_year}-{seq_str}"
        
        # Check if this ID already exists
        if not StaffProfile.objects.filter(employee_id=employee_id).exists():
            return employee_id
        
        # Collision detected, increment sequence and try again
        sequence += 1
        attempt += 1
    
    # Fallback: if max attempts exceeded, raise an error
    raise RuntimeError(
        f"Could not generate unique employee ID for school {school.name} after {max_attempts} attempts."
    )
