import os
from pathlib import Path
import sys

# Import base settings from paletta_core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from paletta_core.settings import *

# Override settings for production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# For production, allow only the IP address of the EC2 instance
ALLOWED_HOSTS = ['18.175.250.8', '127.0.0.1']

# Security settings for production
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

# Database settings - use environment variables for production
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(conn_max_age=600, ssl_require=True)

# AWS S3 Storage Configuration
AWS_STORAGE_ENABLED = os.environ.get('AWS_STORAGE_ENABLED', 'False') == 'True'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'
AWS_DEFAULT_ACL = 'private'
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = AWS_REGION

# Use S3 for static files in production
if not DEBUG and AWS_STORAGE_ENABLED:
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    
    # For media files
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Download link configuration
DOWNLOAD_LINK_EXPIRY_HOURS = int(os.environ.get('DOWNLOAD_LINK_EXPIRY_HOURS', '24'))
DELETE_LOCAL_FILE_AFTER_UPLOAD = os.environ.get('DELETE_LOCAL_FILE_AFTER_UPLOAD', 'True') == 'True'
SEND_UPLOAD_CONFIRMATION_EMAIL = os.environ.get('SEND_UPLOAD_CONFIRMATION_EMAIL', 'True') == 'True'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat schedule for periodic tasks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'cleanup-expired-download-links': {
        'task': 'videos.tasks.cleanup_expired_download_links',
        'schedule': crontab(hour='*/1'),  # Run every hour
    },
    'retry-failed-uploads': {
        'task': 'videos.tasks.retry_failed_uploads',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
}

# Email Configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@paletta.com')

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/paletta.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'videos': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Create logs directory if it doesn't exist
logs_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880000  # 5GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880000  # 5GB 