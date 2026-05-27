import os
from .base import *
from decouple import config

DEBUG = False

# Allow Render domain and localhost for health checks
ALLOWED_HOSTS = [
    'schoolnowmgt.onrender.com',
    'www.schoolnowmgt.onrender.com',
    '127.0.0.1',
    'localhost',
    os.getenv('RENDER_EXTERNAL_HOSTNAME', ''),
]
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # Remove empty strings

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     config('DB_NAME', default='school_db'),
        'USER':     config('DB_USER', default='school_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 0,  # Disable connection pooling on Render
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'ATOMIC_REQUESTS': False,
    }
}

# Security headers — enable once HTTPS is confirmed working
SECURE_SSL_REDIRECT         = True
SESSION_COOKIE_SECURE       = True
CSRF_COOKIE_SECURE          = True
SECURE_HSTS_SECONDS         = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD         = True
SECURE_BROWSER_XSS_FILTER   = True
X_FRAME_OPTIONS             = 'DENY'

# Logging — write errors to console so Render captures them
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'SchoolNowMgt': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST    = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT    = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER',     default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# WhiteNoise configuration for serving static files efficiently
# This allows WhiteNoise to compress files on-the-fly
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = True
WHITENOISE_COMPRESSION_QUALITY = 80

# ────────────────────────────────────────────────────────────────────────────
# PRE-LAUNCH CHECKLIST
# ────────────────────────────────────────────────────────────────────────────
# [ ] DEBUG = False confirmed in prod.py
# [ ] SECRET_KEY is 50+ random characters, not the dev key
# [ ] ALLOWED_HOSTS lists only your real domain(s)
# [ ] PostgreSQL database created and credentials set in .env
# [ ] python manage.py migrate run on production database
# [ ] python manage.py createsuperuser run on production
# [ ] python manage.py collectstatic --noinput run
# [ ] AT_SANDBOX = False and live API key set in .env
# [ ] AT_SENDER_ID registered with Africa's Talking for Uganda
# [ ] HTTPS confirmed working before enabling SECURE_SSL_REDIRECT
# [ ] SECURE_SSL_REDIRECT = True uncommented in prod.py
# [ ] Cron job for send_pending_sms set up on server
# [ ] Media file storage reviewed — Render's free tier disk
#     is ephemeral; move media to Cloudinary or S3 before
#     storing real student photos in production
# [ ] Run: python manage.py check --deploy
#     and resolve all warnings before launch
# ────────────────────────────────────────────────────────────────────────────
