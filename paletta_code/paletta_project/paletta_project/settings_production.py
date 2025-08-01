import os
import sys
from dotenv import load_dotenv
import dj_database_url

# Production settings file for AWS deployment
# Import base settings from paletta_core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from paletta_core.settings_development import *
from paletta_core.storage import MediaStorage

# Load environment variables from .env file
env_path = '/home/ssm-user/Paletta/.env'
load_dotenv(dotenv_path=env_path)

# Override settings for production
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)

# Allow EC2 instance public IP and domain
ALLOWED_HOSTS = [
    'paletta-alb-62461270.eu-west-2.elb.amazonaws.com',
    'paletta.io',
    'www.paletta.io',
]

# Security settings for production
if not DEBUG:
    # Check if the request is already HTTPS
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

# Database settings - use environment variables for production
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Ensure DATABASE_URL is set in production
if not os.environ.get('DATABASE_URL'):
    raise ValueError("DATABASE_URL environment variable not set in production.")

# API Gateway Configuration
API_GATEWAY_URL = os.environ.get('API_GATEWAY_URL')
if not API_GATEWAY_URL:
    # In production, we require the API Gateway URL to be set.
    raise ValueError("API_GATEWAY_URL environment variable not set.")

# Override INSTALLED_APPS to use proper app configurations
INSTALLED_APPS = [
    # Local apps with proper configurations
    'accounts.apps.AccountsConfig',
    'videos.apps.VideosConfig',
    'libraries.apps.LibrariesConfig',
    'orders.apps.OrdersConfig',
    
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',

    # AWS S3 and storage
    'storages',
    'django_ses',
]

# AWS S3 Storage Configuration
AWS_STORAGE_ENABLED = True
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.environ.get('AWS_REGION')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME') # For direct video uploads
AWS_MEDIA_BUCKET_NAME = os.environ.get('AWS_MEDIA_BUCKET_NAME') # For thumbnails and other uploaded images
AWS_STATIC_BUCKET_NAME = os.environ.get('AWS_STATIC_BUCKET_NAME') # For static CSS/JS

# Check for essential AWS settings
if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_STORAGE_BUCKET_NAME, AWS_MEDIA_BUCKET_NAME, AWS_STATIC_BUCKET_NAME]):
    raise ValueError("One or more required AWS environment variables are not set.")

AWS_S3_CUSTOM_DOMAIN = f'{AWS_STATIC_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = AWS_REGION

# Use S3 for static files in production
if AWS_STORAGE_ENABLED:
    # Static files configuration
    STATICFILES_STORAGE = 'paletta_core.storage.StaticStorage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # Media files configuration
    DEFAULT_FILE_STORAGE = 'paletta_core.storage.MediaStorage'
    MEDIA_URL = f'https://{AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com/{MediaStorage.location}/'

# Static file versioning for cache busting
# Change this value whenever you want to force cache invalidation
STATIC_VERSION = '0.0.0'

# Download link configuration - 48 hours for download requests
DOWNLOAD_LINK_EXPIRY_HOURS = int(os.environ.get('DOWNLOAD_LINK_EXPIRY_HOURS', '48'))  # 48 hours for download requests
DOWNLOAD_REQUEST_EXPIRY_HOURS = 48  # Fixed 48-hour expiry for download requests
DELETE_LOCAL_FILE_AFTER_UPLOAD = os.environ.get('DELETE_LOCAL_FILE_AFTER_UPLOAD', 'True') == 'True'
SEND_UPLOAD_CONFIRMATION_EMAIL = os.environ.get('SEND_UPLOAD_CONFIRMATION_EMAIL', 'True') == 'True'

# S3 Multipart Upload Configuration - Performance optimization for large files
S3_MULTIPART_THRESHOLD = int(os.environ.get('S3_MULTIPART_THRESHOLD', '5242880'))  # 5MB default
S3_MULTIPART_CHUNK_SIZE = int(os.environ.get('S3_MULTIPART_CHUNK_SIZE', '104857600'))  # 100MB chunks for large files
S3_MAX_CONCURRENT_PARTS = int(os.environ.get('S3_MAX_CONCURRENT_PARTS', '100'))  # 100 concurrent parts for large files

# AWS SES Configuration for email automation
AWS_SES_ENABLED = os.environ.get('AWS_SES_ENABLED', 'False') == 'True'
AWS_SES_REGION = os.environ.get('AWS_SES_REGION', AWS_REGION)
AWS_SES_SENDER_EMAIL = os.environ.get('AWS_SES_SENDER_EMAIL', 'niklaas@filmbright.com')

# Manager notification email settings
MANAGER_EMAIL = os.environ.get('MANAGER_EMAIL', 'info@filmbright.com')

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
    'cleanup-expired-download-requests': {
        'task': 'orders.tasks.cleanup_expired_download_requests',
        'schedule': crontab(minute='*/120'),  # Run every 2 hours
    },
    'retry-failed-uploads': {
        'task': 'videos.tasks.retry_failed_uploads',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
    },
}

# Email Configuration
# Check if AWS SES should be used based on AWS_SES_ENABLED environment variable
if AWS_SES_ENABLED:
    # Use AWS SES backend for production email sending
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_REGION_NAME = AWS_SES_REGION or AWS_REGION
    AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
    
    # Log SES configuration for production debugging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Email configured for AWS SES in region {AWS_SES_REGION_NAME}")
else:
    # Fallback to environment-specified backend or console
    EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# Default sender email - applies to both SES and other backends  
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'niklaas@filmbright.com')

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
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/ssm-user/Paletta/django-debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
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
# NOTE: Increasing this to a large value without implementing direct-to-S3 uploads
# can cause server instability, as the entire file will be temporarily stored on the server's disk.
FILE_UPLOAD_MAX_MEMORY_SIZE = 274877906944  # 256GB
DATA_UPLOAD_MAX_MEMORY_SIZE = 274877906944  # 256GB

CSRF_TRUSTED_ORIGINS = [
    'http://paletta-alb-62461270.eu-west-2.elb.amazonaws.com',
    'https://paletta-alb-62461270.eu-west-2.elb.amazonaws.com',
    'https://paletta.io',
    'https://www.paletta.io',
]