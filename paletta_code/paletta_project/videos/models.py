from django.db import models
from django.utils import timezone
from accounts.models import User
import os
from django.core.validators import FileExtensionValidator

def category_image_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/category_images/<category_name>/<filename>
    """
    return f'category_images/{instance.name}/{filename}'

# SQL model for category
class Category(models.Model):
  name = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  created_at = models.DateTimeField(default=timezone.now)
  image = models.ImageField(
    upload_to=category_image_path, 
    null=True, 
    blank=True,
    help_text="Upload an image for this category. Recommended size: 200x200px."
  )

  def __str__(self):
    return self.name
  
  class Meta:
    verbose_name_plural = "Categories"

# SQL model for tag
class Tag(models.Model):
  name = models.CharField(max_length=25)

  def __str__(self):
    return self.name

def video_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/videos/user_<id>/<filename>
    return f'videos/user_{instance.uploader.id}/{filename}'

def thumbnail_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/thumbnails/user_<id>/<filename>
    return f'thumbnails/user_{instance.uploader.id}/{filename}'

# SQL model for video
class Video(models.Model):
  STORAGE_STATUS_CHOICES = [
    ('pending', 'Pending Upload'),
    ('uploading', 'Uploading to Storage'),
    ('stored', 'Stored in Deep Storage'),
    ('failed', 'Upload Failed'),
    ('processing', 'Processing'),
  ]

  title = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
  uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
  upload_date = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  tags = models.ManyToManyField(Tag, related_name='videos', blank=True)
  
  # Video file field - now optional as we'll store in deep storage
  video_file = models.FileField(
    upload_to=video_upload_path,
    validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'])],
    null=True,
    blank=True,
    help_text="Temporary storage before uploading to AWS S3 storage"
  )
  
  # Deep storage fields
  storage_url = models.URLField(
    max_length=500, 
    null=True, 
    blank=True, 
    help_text="URL to the video in AWS S3 storage"
  )
  download_link = models.URLField(
    max_length=500, 
    null=True, 
    blank=True, 
    help_text="Temporary download link for the video" # TODO: setup download link
  )
  download_link_expiry = models.DateTimeField(
    null=True, 
    blank=True, 
    help_text="Expiration time for the download link"
  )
  storage_status = models.CharField(
    max_length=20,
    choices=STORAGE_STATUS_CHOICES,
    default='pending',
    help_text="Current status of the video in AWS S3 storage"
  )
  storage_reference_id = models.CharField(
    max_length=255, 
    null=True, 
    blank=True, 
    help_text="Reference ID in the AWS S3 storage system"
  )
  
  # Thumbnail image
  thumbnail = models.ImageField(upload_to=thumbnail_upload_path, null=True, blank=True)
  
  # Additional metadata
  duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
  file_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size in bytes")
  views_count = models.PositiveIntegerField(default=0)
  is_published = models.BooleanField(default=True)

  def __str__(self):
    return self.title
    
  def get_file_extension(self):
    if self.video_file:
        name, extension = os.path.splitext(self.video_file.name)
        return extension[1:].lower()  # Remove the dot and convert to lowercase
    return None

# Video activity log model
class VideoLog(models.Model):
    """
    Model for logging video-related activities for admin tracking.
    """
    LOG_TYPE_CHOICES = [
        ('upload', 'Video Uploaded'),
        ('process', 'Video Processing'),
        ('store', 'Video Stored in S3'),
        ('download', 'Video Download Requested'),
        ('delete', 'Video Deleted'),
        ('error', 'Error Occurred'),
        ('status_change', 'Status Changed'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='video_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    message = models.TextField()
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size in bytes")
    storage_status = models.CharField(max_length=20, null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Video Log"
        verbose_name_plural = "Video Logs"
        
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.video.title} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
