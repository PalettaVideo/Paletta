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
  title = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
  uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
  upload_date = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  tags = models.ManyToManyField(Tag, related_name='videos', blank=True)
  
  # Video file field
  video_file = models.FileField(
    upload_to=video_upload_path,
    validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'])],
    null=True
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
