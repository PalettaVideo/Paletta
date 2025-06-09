from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import setting
from django.conf import settings


class StaticStorage(S3Boto3Storage):
    """Handles static files collected by collectstatic."""
    location = 'static'
    file_overwrite = True
    
    @property
    def bucket_name(self):
        """Lazily load the bucket name from settings to avoid import-time errors."""
        return settings.AWS_STATIC_BUCKET_NAME


class MediaStorage(S3Boto3Storage):
    """Handles user-uploaded media files like thumbnails and logos."""
    location = 'thumbnails'  # Store files in a /thumbnails/ folder
    file_overwrite = False
    # Lazily load the bucket name from settings.
    bucket_name = setting('AWS_MEDIA_BUCKET_NAME')

    @property
    def custom_domain(self):
        """
        Lazily constructs the custom domain from settings to avoid
        initialization errors.
        """
        return f'{settings.AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com'
