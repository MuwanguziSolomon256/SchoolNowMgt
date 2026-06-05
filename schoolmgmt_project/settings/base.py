from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-change-in-production')

AUTH_USER_MODEL = 'SchoolNowMgt.CustomUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
    
    # Third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    'allauth.socialaccount.providers.apple',
    
    # Local apps
    'authentication',
    'teacher_auth',
    'teacher',
    'user_profile',
    'dashboard',
    'curriculum',
    'SchoolNowMgt',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'schoolmgmt_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                # 'allauth.account.context_processors.account',
                # 'allauth.socialaccount.context_processors.socialaccount',
            ],
        },
    },
]

WSGI_APPLICATION = 'schoolmgmt_project.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.'
             'UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.'
             'MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.'
             'CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.'
             'NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-gb'
TIME_ZONE     = 'Africa/Kampala'
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Use standard storage - WhiteNoise will compress and serve efficiently
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Ensure all static files are found and collected
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL          = 'auth:login'
LOGIN_REDIRECT_URL = 'SchoolNowMgt:dashboard'
LOGOUT_REDIRECT_URL = 'auth:login'

# Africa's Talking
AT_USERNAME  = config('AT_USERNAME', default='')
AT_API_KEY   = config('AT_API_KEY', default='')
AT_SENDER_ID = config('AT_SENDER_ID', default='')
AT_SANDBOX   = config('AT_SANDBOX', default=True, cast=bool)

# File upload limits — keeps server storage manageable
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB

# ═════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION & SESSION CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

AUTHENTICATION_BACKENDS = [
    # Default Django backend
    'django.contrib.auth.backends.ModelBackend',
    
    # django-allauth backends
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Session configuration
SESSION_COOKIE_AGE = 2592000  # 30 days in seconds (86400 * 30)
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ═════════════════════════════════════════════════════════════════════════════
# DJANGO-ALLAUTH CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Change to 'mandatory' in production
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Redirect URLs for allauth
ACCOUNT_ADAPTER = 'allauth.account.adapter.DefaultAccountAdapter'
ACCOUNT_LOGIN_REDIRECT_URL = 'SchoolNowMgt:dashboard'
ACCOUNT_LOGOUT_REDIRECT_URL = 'login'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'

# OAuth Provider Configuration
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': '',
        }
    },
    'microsoft': {
        'TENANT': config('MICROSOFT_TENANT', default='common'),
        'SCOPE': ['User.Read'],
        'AUTH_PARAMS': {},
        'APP': {
            'client_id': config('MICROSOFT_CLIENT_ID', default=''),
            'secret': config('MICROSOFT_CLIENT_SECRET', default=''),
            'key': '',
        }
    },
    'apple': {
        'SCOPE': ['email', 'name'],
        'AUTH_PARAMS': {'response_type': 'code id_token'},
        'APP': {
            'client_id': config('APPLE_CLIENT_ID', default=''),
            'secret': config('APPLE_CLIENT_SECRET', default=''),
            'key': '',
        }
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# EMAIL CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)

# SMTP Configuration (for production)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Default sender email
DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default='SchoolNow <noreply@schoolnow.edu>'
)
SERVER_EMAIL = config(
    'SERVER_EMAIL',
    default='SchoolNow Admin <admin@schoolnow.edu>'
)

# Password reset timeout (24 hours)
PASSWORD_RESET_TIMEOUT = 86400
