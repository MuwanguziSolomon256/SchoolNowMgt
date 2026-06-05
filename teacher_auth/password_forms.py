import re
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError


class TeacherPasswordResetForm(PasswordResetForm):
    """
    Password reset form for teachers.
    
    Overrides get_users() to filter results by role == 'teacher',
    preventing accidental password resets to parent or admin accounts.
    """
    
    def get_users(self, email):
        """
        Return users with the given email address and role='teacher'.
        
        This prevents a parent or admin account from receiving a teacher
        password reset email by mistake.
        """
        return (
            u for u in super().get_users(email)
            if u.role == 'teacher'
        )


class TeacherSetPasswordForm(SetPasswordForm):
    """
    Password reset confirmation form for teachers.
    
    Enforces the same password strength validation as teacher registration
    (T-01) to ensure consistency:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one digit
      - At least one special character: ! @ # $ % ^ & * ( ) _ + -
    
    Each rule that fails raises a separate ValidationError.
    """
    
    def clean_password2(self):
        """Validate password strength with separate errors for each rule."""
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            raise ValidationError("Password is required.")
        
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one digit.")
        
        # Check for at least one special character
        special_chars = r'[!@#$%^&*()_+\-]'
        if not re.search(special_chars, password):
            raise ValidationError(
                "Password must contain at least one special character from: ! @ # $ % ^ & * ( ) _ + -"
            )
        
        # Return the result of parent's clean_password2() which validates mismatch
        return super().clean_password2()
