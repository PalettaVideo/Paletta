from django.db import models
from django.utils import timezone
from accounts.models import User
from videos.models import Video
from django.core.exceptions import ValidationError

class Library(models.Model):
    """
    Model representing a video library with its own branding and storage settings.
    """
    STORAGE_TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    # Storage size constants (in bytes)
    GB = 1024 * 1024 * 1024  # 1 GB in bytes
    TB = GB * 1024  # 1 TB in bytes

    BASIC_LIMIT = 100 * GB
    PRO_LIMIT = 1 * TB
    ENTERPRISE_LIMIT = 10 * TB
    
    name = models.CharField(max_length=25, unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_libraries')
    logo = models.ImageField(upload_to='library_logos/', blank=True, null=True)
    # Store color scheme as JSON
    color_scheme = models.JSONField(default=dict, blank=True)
    storage_tier = models.CharField(max_length=20, choices=STORAGE_TIER_CHOICES, default='basic')
    storage_size = models.BigIntegerField(default=100 * GB)  # Default 100GB in bytes
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    videos = models.ManyToManyField(Video, related_name='libraries', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Libraries"

    def __str__(self):
        return self.name
    
    @property
    def storage_size_gb(self):
        """Return the storage size in GB for easier reading."""
        return self.storage_size / self.GB
        
    @property
    def storage_size_tb(self):
        """Return the storage size in TB for larger values."""
        return self.storage_size / self.TB
    
    @property
    def tier_limit(self):
        """Return the maximum limit for the current tier in bytes."""
        if self.storage_tier == 'basic':
            return self.BASIC_LIMIT
        elif self.storage_tier == 'pro':
            return self.PRO_LIMIT
        elif self.storage_tier == 'enterprise':
            return self.ENTERPRISE_LIMIT
        return self.BASIC_LIMIT  # Default to basic
    
    def set_storage_size_display(self):
        """Set the default storage size based on the selected tier."""
        if self.storage_tier == 'basic':
            self.storage_size = self.BASIC_LIMIT
        elif self.storage_tier == 'pro':
            self.storage_size = self.PRO_LIMIT
        elif self.storage_tier == 'enterprise':
            self.storage_size = self.ENTERPRISE_LIMIT
        self.save(update_fields=['storage_size'])

    def clean(self):
        # Set default color scheme if not provided
        if not self.color_scheme:
            self.color_scheme = {
                'primary': '#86B049',
                'secondary': '#FFFFFF',
                'text': '#000000'
            }

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def get_storage_display(self):
        """Return a human-readable storage size string."""
        if self.storage_size >= self.TB:
            return f"{self.storage_size_tb:.2f} TB"
        else:
            return f"{self.storage_size_gb:.2f} GB"


class UserLibraryRole(models.Model):
    """
    Model representing a user's role within a specific library.
    """
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('contributor', 'Contributor'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='library_roles')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('library', 'user')
        verbose_name_plural = "User Library Roles"

    def __str__(self):
        return f"{self.user.username} - {self.library.name} ({self.get_role_display()})"
