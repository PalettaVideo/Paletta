from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Handles static files collected by collectstatic."""
    location = 'static'
    file_overwrite = True
    bucket_name = settings.AWS_STATIC_BUCKET_NAME

class MediaStorage(S3Boto3Storage):
    """Handles user-uploaded media files like thumbnails and logos."""
    location = 'uploaded-media'  # Store files in the /uploaded-media/ folder
    file_overwrite = False
    bucket_name = settings.AWS_STATIC_BUCKET_NAME  # Use the static bucket
    # Set the domain to the static bucket for correct URL generation
    custom_domain = f'{settings.AWS_STATIC_BUCKET_NAME}.s3.amazonaws.com'
