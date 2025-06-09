from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Handles static files collected by collectstatic."""
    location = 'static'
    file_overwrite = True
    bucket_name = settings.AWS_STATIC_BUCKET_NAME

class MediaStorage(S3Boto3Storage):
    """Handles user-uploaded media files like thumbnails and logos."""
    location = 'thumbnails'  # Store files in a /thumbnails/ folder
    file_overwrite = False
    bucket_name = settings.AWS_MEDIA_BUCKET_NAME  # Use the new media bucket
    custom_domain = f'{settings.AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com'
