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
    
    Manages video libraries with storage tiers, categories, and user roles.
    """
    STORAGE_TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    CATEGORY_SOURCE_CHOICES = [
        ('paletta_style', 'Use Paletta Style Categories'),
        ('custom', 'Create My Own Categories'),
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
    
    # Category source selection
    category_source = models.CharField(
        max_length=20, 
        choices=CATEGORY_SOURCE_CHOICES, 
        default='custom',
        help_text="Choose the source for video categories in this library"
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
        USED BY: Category setup logic and template rendering
        
        Returns True for libraries named 'paletta' (case-insensitive).
        """
        return self.name.lower() == 'paletta'
    
    @property
    def uses_paletta_categories(self):
        """
        BACKEND/FRONTEND-READY: Check if library uses Paletta-style categories.
        MAPPED TO: Category management logic
        USED BY: setup_default_categories() and admin interface
        
        Returns True if category_source is 'paletta_style' or is main Paletta library.
        """
        return self.category_source == 'paletta_style' or self.is_paletta_library
    
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
        
        Sets default color scheme and enforces Paletta library category rules.
        """
        # Set default color scheme if not provided
        if not self.color_scheme:
            self.color_scheme = {
                'primary': '#86B049',
                'secondary': '#FFFFFF',
                'text': '#000000'
            }
        
        # Paletta library must use Paletta categories
        if self.is_paletta_library and self.category_source != 'paletta_style':
            self.category_source = 'paletta_style'

    def save(self, *args, **kwargs):
        """
        BACKEND-READY: Enhanced save method with automatic category setup.
        MAPPED TO: Model creation/update process
        USED BY: All library create/update operations
        
        Runs validation and sets up default categories for new libraries.
        """
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create default categories based on source choice
        if is_new:
            self.setup_default_categories()
    
    def setup_default_categories(self):
        """
        BACKEND-READY: Initialize default categories based on library type.
        MAPPED TO: Library creation process
        USED BY: save() method for new libraries
        
        Creates appropriate default categories and content types for the library.
        """
        from videos.models import Category, PalettaCategory, ContentType
        
        # Always create all content types (they're global)
        content_types_data = [
            'campus_life', 'teaching_learning', 'research_innovation', 
            'city_environment', 'aerial_establishing', 'people_portraits',
            'culture_events', 'workspaces_facilities', 'cutaways_abstracts', 
            'historical_archive'
        ]
        
        for ct_code in content_types_data:
            ContentType.objects.get_or_create(code=ct_code)
        
        # Create all Paletta categories (they're global) INCLUDING PRIVATE
        paletta_categories_data = [
            'private',  # ALWAYS CREATE PRIVATE CATEGORY
            'people_community', 'buildings_architecture', 'classrooms_learning',
            'field_trips_outdoor', 'events_conferences', 'research_innovation_spaces',
            'technology_equipment', 'everyday_campus', 'urban_natural_environments',
            'backgrounds_abstracts'
        ]
        
        for pc_code in paletta_categories_data:
            PalettaCategory.objects.get_or_create(code=pc_code)
        
        # Create Category objects for THIS specific library
        if self.uses_paletta_categories:
            # For Paletta-style libraries, create Category objects corresponding to PalettaCategories
            for pc_code in paletta_categories_data:
                paletta_cat = PalettaCategory.objects.get(code=pc_code)
                Category.objects.get_or_create(
                    subject_area=pc_code,
                    library=self,
                    defaults={
                        'description': f'{paletta_cat.display_name} category for {self.name}',
                        'is_active': True
                    }
                )
        else:
            # For custom libraries, only create the private category by default
            Category.objects.get_or_create(
                subject_area='private',
                library=self,
                defaults={
                    'description': 'Private videos. Only you and library administrators can see these videos.',
                    'is_active': True
                }
            )
    
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
