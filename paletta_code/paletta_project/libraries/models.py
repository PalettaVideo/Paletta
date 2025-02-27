from django.db import models
from django.utils import timezone
from accounts.models import User
from videos.models import Video

class Library(models.Model):
  name = models.CharField(max_length=25)
  description = models.TextField(blank=True)
  owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_libraries')
#  logo = models.ImageField(upload_to='library_logos/', blank=True, null=True)
#  primary_color = models.CharField(max_length=7, default='#000000')
#  secondary_color = models.CharField(max_length=7, default='#000000')
  created_at = models.DateTimeField(default=timezone.now)
  updated_at = models.DateTimeField(auto_now=True)
  videos = models.ManyToManyField(Video, related_name='libraries', blank=True)

  class Meta:
    verbose_name_plural = "Libraries"

  def __str__(self):
    return self.name


class LibraryMember(models.Model):
  ROLE_CHOICES = [
    ('admin', 'Administrator'),
    ('contributor', 'Contributor'),
    ('customer', 'Customer'),
  ]

  library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='members')
  user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_memberships')
  role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
  added_at = models.DateTimeField(default=timezone.now)

  class Meta:
    unique_together = ('library', 'user')
    verbose_name_plural = "Library Members"

  def __str__(self):
    return f"{self.user.username} - {self.library.name} ({self.role})"
