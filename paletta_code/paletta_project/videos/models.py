from django.db import models
from django.utils import timezone
from accounts.models import User
import os
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from paletta_core.storage import get_media_storage
from django.core.exceptions import ValidationError

def category_image_path(instance, filename):
    """
    BACKEND-READY: Generates upload path for category images.
    MAPPED TO: Internal storage function
    USED BY: Category.image field
    
    Creates organized file paths: category_images/<library_name>/<category_slug>/<filename>
    Required fields: instance (Category), filename (str)
    """
    if hasattr(instance, 'subject_area'):
        category_name = f"{instance.subject_area}"
    else:
        category_name = instance.slug
    return f'category_images/{instance.library.name}/{category_name}/{filename}'

# Content Type model for multi-select support
class ContentType(models.Model):
    """Model representing content types that can be applied to videos"""
    
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
    
    code = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['code']
        
    @property
    def display_name(self):
        return dict(self.CONTENT_TYPE_CHOICES).get(self.code, self.code)
    
    def __str__(self):
        return self.display_name

# Paletta Default Categories model
class PalettaCategory(models.Model):
    """Model representing Paletta's default predefined categories"""
    
    PALETTA_CATEGORY_CHOICES = [
        ('people_community', 'People and Community'),
        ('buildings_architecture', 'Buildings & Architecture'),
        ('classrooms_learning', 'Classrooms & Learning Spaces'),
        ('field_trips_outdoor', 'Field Trips & Outdoor Learning'),
        ('events_conferences', 'Events & Conferences'),
        ('research_innovation_spaces', 'Research & Innovation Spaces'),
        ('technology_equipment', 'Technology & Equipment'),
        ('everyday_campus', 'Everyday Campus Life'),
        ('urban_natural_environments', 'Urban & Natural Environments'),
        ('backgrounds_abstracts', 'Backgrounds & Abstracts'),
        ('private', 'Private'),  # Private category for Paletta libraries
    ]
    
    code = models.CharField(max_length=50, choices=PALETTA_CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['code']
        verbose_name = "Paletta Category"
        verbose_name_plural = "Paletta Categories"
        
    @property
    def display_name(self):
        return dict(self.PALETTA_CATEGORY_CHOICES).get(self.code, self.code)
    
    def __str__(self):
        return self.display_name

# Updated Category model for Subject Area
class Category(models.Model):
    """Model representing subject area categories within a specific library."""
    
    # Subject area choices (single selection)
    SUBJECT_AREA_CHOICES = [
        # Special Categories
        ('private', 'Private'),  # Private category for all libraries
        ('custom', 'Custom'),  # Custom category type
        # Academic Subject Areas
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
        
        # Paletta Categories (for Paletta-style libraries)
        ('people_community', 'People and Community'),
        ('buildings_architecture', 'Buildings & Architecture'),
        ('classrooms_learning', 'Classrooms & Learning Spaces'),
        ('field_trips_outdoor', 'Field Trips & Outdoor Learning'),
        ('events_conferences', 'Events & Conferences'),
        ('research_innovation_spaces', 'Research & Innovation Spaces'),
        ('technology_equipment', 'Technology & Equipment'),
        ('everyday_campus', 'Everyday Campus Life'),
        ('urban_natural_environments', 'Urban & Natural Environments'),
        ('backgrounds_abstracts', 'Backgrounds & Abstracts'),
    ]
    
    subject_area = models.CharField(max_length=50, choices=SUBJECT_AREA_CHOICES)
    custom_name = models.CharField(max_length=100, blank=True, null=True, help_text="Custom category name (used when subject_area is 'custom')")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to=category_image_path, blank=True, null=True, storage=get_media_storage)
    library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='categories')
    is_active = models.BooleanField(default=True, help_text="Whether this category is available for selection")
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['subject_area', 'custom_name']
        unique_together = [['subject_area', 'library'], ['custom_name', 'library']]
    
    @property
    def display_name(self):
        """Generate display name from subject area or custom name"""
        if self.subject_area == 'custom' and self.custom_name:
            return self.custom_name
        return dict(self.SUBJECT_AREA_CHOICES).get(self.subject_area, self.subject_area)
    
    @property
    def slug(self):
        """Generate URL-friendly slug"""
        if self.subject_area == 'custom' and self.custom_name:
            from django.utils.text import slugify
            return slugify(self.custom_name)
        return self.subject_area
    
    def clean(self):
        """Validate that custom categories have a custom_name"""
        if self.subject_area == 'custom' and not self.custom_name:
            raise ValidationError({'custom_name': 'Custom name is required when subject area is "custom".'})
        if self.subject_area != 'custom' and self.custom_name:
            # Clear custom_name if not using custom subject area
            self.custom_name = None
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.display_name} ({self.library.name})"
        
    def get_absolute_url(self):
        return reverse('category', kwargs={'library_name': self.library.name, 'category_name': self.slug})

# SQL model for tag
class Tag(models.Model):
    name = models.CharField(max_length=25)
    library = models.ForeignKey('libraries.Library', on_delete=models.CASCADE, related_name='tags')
    
    class Meta:
        unique_together = ['name', 'library']

    def __str__(self):
        return f"{self.name} ({self.library.name})"

def video_upload_path(instance, filename):
    """
    BACKEND-READY: Generates upload path for video files.
    MAPPED TO: Internal storage function  
    USED BY: Video.video_file field
    
    Creates organized file paths: videos/library_<id>/user_<id>/<filename>
    Required fields: instance (Video), filename (str)
    """
    # File will be uploaded to MEDIA_ROOT/videos/library_<id>/user_<id>/<filename>
    return f'videos/library_{instance.library.id}/user_{instance.uploader.id}/{filename}'

def thumbnail_upload_path(instance, filename):
    """
    BACKEND-READY: Generates upload path for video thumbnails.
    MAPPED TO: Internal storage function
    USED BY: Video.thumbnail field
    
    Creates organized file paths: thumbnails/library_<id>/user_<id>/<filename>
    Required fields: instance (Video), filename (str)
    """
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
  
  # New dual-category structure
  subject_area = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos', help_text="Required: Select one subject area")
  content_types = models.ManyToManyField(ContentType, related_name='videos', help_text="Required: Select 1-3 content types")
  paletta_category = models.ForeignKey(PalettaCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='videos', help_text="For Paletta library videos only")
  
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

  def clean(self):
    """Custom validation for video model"""
    super().clean()
    
    # Validate content types count (1-3)
    if self.pk:  # Only validate if object exists (has been saved)
        content_count = self.content_types.count()
        if content_count == 0:
            raise ValidationError("At least one content type must be selected.")
        if content_count > 3:
            raise ValidationError("Maximum of 3 content types can be selected.")

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
      BACKEND/FRONTEND-READY: Generates temporary streaming URL for S3-stored videos.
      MAPPED TO: Internal method called by templates
      USED BY: Video detail templates and API responses
      
      Creates temporary S3 presigned URL for video streaming (1 hour expiry).
      Required fields: storage_status='stored', storage_reference_id
      """
      if self.storage_status == 'stored' and self.storage_reference_id:
          from .services import AWSCloudStorageService
          storage_service = AWSCloudStorageService()
          return storage_service.generate_streaming_url(self)
      return None
      
  @property
  def display_categories(self):
      """Get display string for all categories"""
      categories = []
      if self.subject_area:
          categories.append(f"Subject: {self.subject_area.display_name}")
      if self.content_types.exists():
          content_names = [ct.display_name for ct in self.content_types.all()]
          categories.append(f"Content: {', '.join(content_names)}")
      if self.paletta_category:
          categories.append(f"Paletta: {self.paletta_category.display_name}")
      return " | ".join(categories)
  
  @property
  def is_private(self):
      """Check if this video is in a private category"""
      if self.paletta_category and self.paletta_category.code == 'private':
          return True
      if self.subject_area and self.subject_area.subject_area == 'private':
          return True
      return False
    
  def delete(self, *args, **kwargs):
    """
    BACKEND-READY: Enhanced delete method with file cleanup.
    MAPPED TO: Model deletion cascade
    USED BY: Admin interface and programmatic deletions
    
    Removes video files from filesystem and S3 storage when model is deleted.
    Handles missing files gracefully with proper logging.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Delete S3 files first if they exist
    if self.storage_status == 'stored' and self.storage_reference_id:
        try:
            from .services import AWSCloudStorageService
            storage_service = AWSCloudStorageService()
            storage_service.s3_client.delete_object(
                Bucket=storage_service.bucket_name,
                Key=self.storage_reference_id
            )
            logger.info(f"Deleted video from S3: {self.storage_reference_id}")
        except Exception as e:
            logger.error(f"Error deleting video from S3 {self.storage_reference_id}: {e}")
    
    # Delete the model instance first
    super().delete(*args, **kwargs)
    
    # Delete files using Django's storage backend (works with both local and S3)
    if self.video_file:
        try:
            self.video_file.delete(save=False)
            logger.info(f"Deleted video file: {self.video_file.name}")
        except Exception as e:
            logger.error(f"Error deleting video file {self.video_file.name}: {e}")
    
    if self.thumbnail:
        try:
            self.thumbnail.delete(save=False)
            logger.info(f"Deleted thumbnail file: {self.thumbnail.name}")
        except Exception as e:
            logger.error(f"Error deleting thumbnail file {self.thumbnail.name}: {e}")

class VideoTag(models.Model):
    """Model representing the many-to-many relationship between videos and tags."""
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['video', 'tag']

    def __str__(self):
        return f"{self.video.title} - {self.tag.name}"


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
        return f"{self.video.title} - {self.get_log_type_display()} ({self.timestamp})"
