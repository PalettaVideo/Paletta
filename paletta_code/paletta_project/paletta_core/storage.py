from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from django.core.files.storage import default_storage


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
    location = 'media'
    file_overwrite = False

    @property
    def bucket_name(self):
        """Lazily load the bucket name from settings to avoid import-time errors."""
        return settings.AWS_MEDIA_BUCKET_NAME

    @property
    def custom_domain(self):
        """
        Lazily constructs the custom domain from settings to avoid
        initialization errors.
        """
        return f'{settings.AWS_MEDIA_BUCKET_NAME}.s3.amazonaws.com'


def get_media_storage():
    """
    Returns the appropriate storage class based on whether AWS is enabled.
    This prevents import-time errors when AWS settings are not available.
    """
    aws_enabled = getattr(settings, 'AWS_STORAGE_ENABLED', False)
    if aws_enabled:
        return MediaStorage()
    else:
        return default_storage
