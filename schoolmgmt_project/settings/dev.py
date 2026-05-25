from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Show emails in terminal instead of sending them
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable SMS sending in dev — log to console instead
# In sms_service.py, check settings.AT_SANDBOX and print rather
# than call the API if a DEV_SMS_MOCK env var is set.
DEV_SMS_MOCK = True
