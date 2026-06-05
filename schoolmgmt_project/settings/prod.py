import os
from .base import *
from decouple import config

DEBUG = False

# Allow PythonAnywhere domain and localhost for health checks
ALLOWED_HOSTS = [
    'msolomon.pythonanywhere.com',
    'www.msolomon.pythonanywhere.com',
    '127.0.0.1',
    'localhost',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.contrib.auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'SchoolNowMgt': {
            'handlers': ['console'],
            'level': 'DEBUG',
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
