from django.db import models
from django.utils import timezone
from accounts.models import User
from videos.models import Video
from django.core.exceptions import ValidationError
from paletta_core.storage import get_media_storage

class Library(models.Model):
    """
    BACKEND/FRONTEND-READY: Core library model for video collections.
    MAPPED TO: /api/libraries/ endpoints
    USED BY: All library-related views and templates
    
    Manages video libraries with storage tiers, content types, and user roles.
    """
    STORAGE_TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    CONTENT_SOURCE_CHOICES = [
        ('paletta_style', 'Use Paletta Style Content Types'),
        ('custom', 'Create My Own Content Types'),
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
    logo = models.ImageField(upload_to='library_logos/', blank=True, null=True, storage=get_media_storage)
    # Store color scheme as JSON
    color_scheme = models.JSONField(default=dict, blank=True)
    storage_tier = models.CharField(max_length=20, choices=STORAGE_TIER_CHOICES, default='basic')
    storage_size = models.BigIntegerField(default=100 * GB)  # Default 100GB in bytes
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    videos = models.ManyToManyField(Video, related_name='libraries', blank=True)
    is_active = models.BooleanField(default=True)
    
    # Content source selection
    content_source = models.CharField(
        max_length=20, 
        choices=CONTENT_SOURCE_CHOICES, 
        default='custom',
        help_text="Choose the source for video content types in this library"
    )

    class Meta:
        verbose_name_plural = "Libraries"

    def __str__(self):
        return self.name
    
    @property
    def is_paletta_library(self):
        """
        BACKEND/FRONTEND-READY: Check if this is the main Paletta library.
        MAPPED TO: Template context and API responses
        USED BY: Content setup logic and template rendering
        
        Returns True for libraries named 'paletta' (case-insensitive).
        """
        return self.name.lower() == 'paletta'
    
    @property
    def uses_paletta_categories(self):
        """
        BACKEND/FRONTEND-READY: Check if library uses Paletta-style content types.
        MAPPED TO: Content management logic
        USED BY: setup_default_categories() and admin interface
        
        Returns True if content_source is 'paletta_style' or is main Paletta library.
        """
        return self.content_source == 'paletta_style' or self.is_paletta_library
    
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
        limits = {
            'basic': self.BASIC_LIMIT,
            'pro': self.PRO_LIMIT,
            'enterprise': self.ENTERPRISE_LIMIT
        }
        return limits.get(self.storage_tier, self.BASIC_LIMIT)
    
    def set_storage_size_display(self):
        """
        BACKEND-READY: Update storage size based on selected tier.
        MAPPED TO: Admin interface save action
        USED BY: LibraryAdmin.save_model()
        
        Automatically sets storage_size to tier default and saves model.
        """
        tier_sizes = {
            'basic': self.BASIC_LIMIT,
            'pro': self.PRO_LIMIT,
            'enterprise': self.ENTERPRISE_LIMIT
        }
        self.storage_size = tier_sizes.get(self.storage_tier, self.BASIC_LIMIT)
        self.save(update_fields=['storage_size'])

    def clean(self):
        """
        BACKEND-READY: Model validation and default value setting.
        MAPPED TO: Model save process
        USED BY: Django model validation system
        
        Sets default color scheme and enforces Paletta library content rules.
        """
        # Set default color scheme if not provided
        if not self.color_scheme:
            self.color_scheme = {
                'primary': '#86B049',
                'secondary': '#FFFFFF',
                'text': '#000000'
            }
        
        # Paletta library must use Paletta content types
        if self.is_paletta_library and self.content_source != 'paletta_style':
            self.content_source = 'paletta_style'

    def save(self, *args, **kwargs):
        """
        BACKEND-READY: Enhanced save method with automatic content setup.
        MAPPED TO: Model creation/update process
        USED BY: All library create/update operations
        
        Runs validation and sets up default content types for new libraries.
        """
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create default content types based on source choice
        if is_new:
            self.setup_default_categories()
    
    def setup_default_categories(self):
        """
        BACKEND-READY: Initialize default content types for the library.
        MAPPED TO: Library creation process
        USED BY: save() method for new libraries
        
        Creates library-specific content types based on the content type list.
        Ensures all required content types exist in the system (they're global).
        """
        from videos.models import ContentType
        
        # Create all content types (they're global and available to all libraries)
        content_types_data = [
            'private', 'campus_life', 'teaching_learning', 'research_innovation', 
            'city_environment', 'aerial_establishing', 'people_portraits',
            'culture_events', 'workspaces_facilities', 'cutaways_abstracts', 
            'historical_archive'
        ]
        
        for ct_code in content_types_data:
            ContentType.objects.get_or_create(code=ct_code)
    
    def get_storage_display(self):
        """
        BACKEND/FRONTEND-READY: Get human-readable storage size string.
        MAPPED TO: Admin interface and API responses
        USED BY: Template rendering and serializers
        
        Returns formatted storage size (e.g., "1.5 TB" or "500.00 GB").
        """
        if self.storage_size >= self.TB:
            return f"{self.storage_size_tb:.2f} TB"
        else:
            return f"{self.storage_size_gb:.2f} GB"
    



class UserLibraryRole(models.Model):
    """
    BACKEND/FRONTEND-READY: User role assignments within libraries.
    MAPPED TO: /api/roles/ endpoints
    USED BY: Permission checking and library management
    
    Manages administrator and contributor roles for library access control.
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
