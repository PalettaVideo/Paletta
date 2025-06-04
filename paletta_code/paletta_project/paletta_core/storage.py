from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = 'static'
    file_overwrite = True
    bucket_name = settings.AWS_STATIC_BUCKET_NAME

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME # intended to use 'paletta-videos' s3 bucket
