from django.db import models
from django.utils import timezone
from accounts.models import User
from videos.models import Video
from django.core.exceptions import ValidationError
from paletta_core.storage import get_media_storage

class Library(models.Model):
    """
    Model representing a video library with its own branding and storage settings.
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
        """Check if this is the main Paletta library"""
        return self.name.lower() == 'paletta'
    
    @property
    def uses_paletta_categories(self):
        """Check if this library uses Paletta style categories"""
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
        
        # Paletta library must use Paletta categories
        if self.is_paletta_library and self.category_source != 'paletta_style':
            self.category_source = 'paletta_style'

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Create default categories based on source choice
        if is_new:
            self.setup_default_categories()
    
    def setup_default_categories(self):
        """Set up default categories based on the library's category source"""
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
            'people_community', 'buildings_architecture', 'classrooms_learning',
            'field_trips_outdoor', 'events_conferences', 'research_innovation_spaces',
            'technology_equipment', 'everyday_campus', 'urban_natural_environments',
            'backgrounds_abstracts', 'private'  # ALWAYS CREATE PRIVATE CATEGORY
        ]
        
        for pc_code in paletta_categories_data:
            PalettaCategory.objects.get_or_create(code=pc_code)
        
        # ALWAYS create a Private category for this specific library (both types need this)
        Category.objects.get_or_create(
            subject_area='private',
            library=self,
            defaults={
                'description': 'Private videos. Only you and library administrators can see these videos.',
                'is_active': True
            }
        )
        
        # For custom libraries, only create the private category by default
        # Other categories will be created when the user selects them during library creation
        # For Paletta libraries, they will use PalettaCategory objects + the private Category as backup
        
    def get_storage_display(self):
        """Return a human-readable storage size string."""
        if self.storage_size >= self.TB:
            return f"{self.storage_size_tb:.2f} TB"
        else:
            return f"{self.storage_size_gb:.2f} GB"
    
    def get_private_category(self):
        """Get the private category for this library"""
        from videos.models import Category, PalettaCategory
        
        if self.uses_paletta_categories:
            # For Paletta libraries, return the private PalettaCategory
            try:
                return PalettaCategory.objects.get(code='private')
            except PalettaCategory.DoesNotExist:
                # Create it if it doesn't exist
                return PalettaCategory.objects.create(code='private')
        else:
            # For custom libraries, return the private Category
            try:
                return Category.objects.get(subject_area='private', library=self)
            except Category.DoesNotExist:
                # Create it if it doesn't exist
                return Category.objects.create(
                    subject_area='private',
                    library=self,
                    is_active=True
                )


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
