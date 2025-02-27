from django.db import models
from django.utils import timezone
from accounts.models import User

class Category(models.Model):
  name = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  created_at = models.DateTimeField(default=timezone.now)

  def __str__(self):
    return self.name
  
  class Meta:
    verbose_name_plural = "Categories"

class Tag(models.Model):
  name = models.CharField(max_length=25)

  def __str__(self):
    return self.name

class Video(models.Model):
  title = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='videos')
  uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
  upload_date = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  tags = models.ManyToManyField(Tag, related_name='videos')

  def __str__(self):
    return self.title
