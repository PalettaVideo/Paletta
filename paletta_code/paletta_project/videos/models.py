from django.db import models
from django.utils import timezone
from accounts.models import User
import os
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from paletta_core.storage import get_media_storage

def category_image_path(instance, filename):
    """
    File will be uploaded to MEDIA_ROOT/category_images/<library_name>/<subject_area>_<content_type>/<filename>
    """
    category_name = f"{instance.subject_area}_{instance.content_type}"
    return f'category_images/{instance.library.name}/{category_name}/{filename}'

# Fixed enums for categories
class Category(models.Model):
    """Model representing predefined video categories within a specific library."""
    
    # Subject area choices (single selection)
    SUBJECT_AREA_CHOICES = [
        ('engineering_sciences', 'Engineering Sciences'),
        ('mathematical_physical_sciences', 'Mathematical & Physical Sciences'),
        ('medical_sciences', 'Medical Sciences'),
        ('life_sciences', 'Life Sciences'),
        ('brain_sciences', 'Brain Sciences'),
        ('built_environment', 'Built Environment'),
        ('population_health', 'Population Health'),
        ('arts_humanities', 'Arts & Humanities'),
        ('social_historical_sciences', 'Social & Historical Sciences'),
        ('education', 'Education'),
        ('fine_art', 'Fine Art'),
        ('law', 'Law'),
        ('business', 'Business'),
    ]
    
    # Format/Content type choices (single or multi-select)
    CONTENT_TYPE_CHOICES = [
        ('campus_life', 'Campus Life'),
        ('teaching_learning', 'Teaching & Learning'),
        ('research_innovation', 'Research & Innovation'),
        ('city_environment', 'City & Environment'),
        ('aerial_establishing', 'Aerial & Establishing Shots'),
        ('people_portraits', 'People & Portraits'),
        ('culture_events', 'Culture & Events'),
        ('workspaces_facilities', 'Workspaces & Facilities'),
        ('cutaways_abstracts', 'Cutaways & Abstracts'),
        ('historical_archive', 'Historical & Archive'),
    ]
    
    # Keep the old name field temporarily for migration
    name = models.CharField(max_length=25)  # Original field, will be removed later
    subject_area = models.CharField(max_length=50, choices=SUBJECT_AREA_CHOICES, null=True, blank=True)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True, storage=get_media_storage)
    library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='categories')
    is_active = models.BooleanField(default=True, help_text="Whether this category is available for selection")
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['subject_area', 'content_type']
        # Keep old constraint temporarily, will be updated in final migration
        unique_together = ['name', 'library']
    
    @property
    def display_name(self):
        """Generate display name from subject area and content type"""
        if self.subject_area and self.content_type:
            subject_display = dict(self.SUBJECT_AREA_CHOICES).get(self.subject_area, self.subject_area)
            content_display = dict(self.CONTENT_TYPE_CHOICES).get(self.content_type, self.content_type)
            return f"{subject_display} - {content_display}"
        return self.name  # Fallback to old name field during transition
    
    @property
    def slug(self):
        """Generate URL-friendly slug"""
        return f"{self.subject_area}_{self.content_type}"
    
    def __str__(self):
        return f"{self.display_name} ({self.library.name})"
        
    def get_absolute_url(self):
        return reverse('category', kwargs={'library_name': self.library.name, 'category_name': self.slug})
    
    @classmethod
    def get_available_combinations(cls):
        """Get all available subject area and content type combinations"""
        combinations = []
        for subject_code, subject_name in cls.SUBJECT_AREA_CHOICES:
            for content_code, content_name in cls.CONTENT_TYPE_CHOICES:
                combinations.append({
                    'subject_area': subject_code,
                    'content_type': content_code,
                    'display_name': f"{subject_name} - {content_name}",
                    'slug': f"{subject_code}_{content_code}"
                })
        return combinations

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
    ('processing_failed', 'Processing Failed'),
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
  storage_url = models.URLField(max_length=1024, blank=True, null=True)
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
    max_length=1024, 
    null=True, 
    blank=True, 
    help_text="Reference ID in the AWS S3 storage system"
  )
  
  # Thumbnail image
  thumbnail = models.ImageField(upload_to=thumbnail_upload_path, null=True, blank=True, storage=get_media_storage)
  
  # Additional metadata
  duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds")
  file_size = models.PositiveIntegerField(null=True, blank=True, help_text="Size in bytes")
  resolution = models.CharField(max_length=20, null=True, blank=True, help_text="Video resolution, e.g., 1920x1080")
  frame_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Frame rate, e.g., 29.97")
  views_count = models.PositiveIntegerField(default=0)
  format = models.CharField(max_length=10, blank=True, null=True)

  def __str__(self):
    return self.title
    
  def get_file_extension(self):
    if self.video_file:
        _, extension = os.path.splitext(self.video_file.name)
        return extension[1:].lower()  # Remove the dot and convert to lowercase
    if self.storage_reference_id:
        _, extension = os.path.splitext(self.storage_reference_id)
        return extension[1:].lower()
    return None
    
  def get_streaming_url(self):
      """
      Generates a temporary streaming URL for a video stored in S3.
      This is intended for use in Django templates.
      """
      if self.storage_status == 'stored' and self.storage_reference_id:
          from .services import AWSCloudStorageService
          storage_service = AWSCloudStorageService()
          return storage_service.generate_streaming_url(self)
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
