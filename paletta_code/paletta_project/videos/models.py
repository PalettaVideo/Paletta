from django.db import models
from django.utils import timezone
from accounts.models import User
import os
from django.core.validators import FileExtensionValidator
from django.urls import reverse

def category_image_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/category_images/<library_name>/<category_name>/<filename>
    """
    return f'category_images/{instance.library.name}/{instance.name}/{filename}'

# SQL model for category
class Category(models.Model):
    """Model representing a video category within a specific library."""
    name = models.CharField(max_length=25)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True)
    library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='categories')
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        # Ensure name is unique per library
        unique_together = ['name', 'library']
    
    def __str__(self):
        return f"{self.name} ({self.library.name})"
        
    def get_absolute_url(self):
        return reverse('category', kwargs={'library_name': self.library.name, 'category_name': self.name.lower()})

# SQL model for tag
class Tag(models.Model):
    name = models.CharField(max_length=25)
    library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='tags')
    
    class Meta:
        unique_together = ['name', 'library']

    def __str__(self):
        return f"{self.name} ({self.library.name})"

def video_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/videos/library_<id>/user_<id>/<filename>
    return f'videos/library_{instance.library.id}/user_{instance.uploader.id}/{filename}'

def thumbnail_upload_path(instance, filename):
    # File will be uploaded to MEDIA_ROOT/thumbnails/library_<id>/user_<id>/<filename>
    return f'thumbnails/library_{instance.library.id}/user_{instance.uploader.id}/{filename}'

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
  tags = models.ManyToManyField(Tag, through='VideoTag', related_name='videos')
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
  library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='library_videos')
  uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
  upload_date = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  
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
    
  def delete(self, *args, **kwargs):
    """
    Override delete method to also remove physical files from the filesystem.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Store file paths before deletion
    video_path = None
    thumbnail_path = None
    
    # Get the file paths if they exist
    if self.video_file:
        try:
            video_path = self.video_file.path
        except Exception as e:
            logger.error(f"Error getting video file path during deletion: {e}")
    
    if self.thumbnail:
        try:
            thumbnail_path = self.thumbnail.path
        except Exception as e:
            logger.error(f"Error getting thumbnail path during deletion: {e}")
    
    # Delete from AWS S3 if needed
    if self.storage_url and self.storage_reference_id:
        from .services import AWSCloudStorageService
        try:
            storage_service = AWSCloudStorageService()
            storage_service.delete_from_storage(self)
            logger.info(f"Deleted video {self.id} from AWS S3 storage")
        except Exception as e:
            logger.error(f"Error deleting video {self.id} from AWS S3: {e}")
    
    # Delete the model from the database
    super().delete(*args, **kwargs)
    
    # After model deletion, delete the physical files
    if video_path and os.path.exists(video_path):
        try:
            os.remove(video_path)
            logger.info(f"Deleted video file from filesystem: {video_path}")
        except Exception as e:
            logger.error(f"Error deleting video file: {e}")
    
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            os.remove(thumbnail_path)
            logger.info(f"Deleted thumbnail from filesystem: {thumbnail_path}")
        except Exception as e:
            logger.error(f"Error deleting thumbnail file: {e}")

# Adding the VideoTag and Upload models from the new schema
class VideoTag(models.Model):
    """Model representing the many-to-many relationship between videos and tags."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['video', 'tag']
        
    def __str__(self):
        return f"{self.video.title} - {self.tag.name}"

class Upload(models.Model):
    """Model representing the upload process for a video."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='uploads')
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploads')
    upload_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.video.title} - {self.get_status_display()}"

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
