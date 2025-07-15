from django.contrib import admin
from django.forms import ModelForm
from .models import Library, UserLibraryRole

class LibraryAdminForm(ModelForm):
    """
    BACKEND-READY: Custom admin form for Library model.
    MAPPED TO: Django Admin interface
    USED BY: LibraryAdmin class
    
    Provides enhanced form handling for library administration.
    """
    class Meta:
        model = Library
        fields = '__all__'

class LibraryAdmin(admin.ModelAdmin):
    """
    BACKEND-READY: Enhanced admin interface for Library management.
    MAPPED TO: /admin/libraries/library/
    USED BY: Django Admin panel
    
    Provides comprehensive library management with filtering and custom displays.
    """
    form = LibraryAdminForm
    list_display = ('name', 'owner', 'category_source', 'created_at', 'storage_tier', 'get_storage_display', 'is_active')
    list_filter = ['owner', 'storage_tier', 'category_source', 'is_active']
    search_fields = ('name', 'description')
    readonly_fields = ('storage_size_display', 'is_paletta_library', 'uses_paletta_categories')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner', 'logo', 'is_active')
        }),
        ('Category Settings', {
            'fields': ('category_source', 'is_paletta_library', 'uses_paletta_categories'),
            'description': 'Configure how categories are managed for this library.'
        }),
        ('Storage Settings', {
            'fields': ('storage_tier', 'storage_size_display',)
        }),
        ('Appearance', {
            'fields': ('color_scheme',),
            'classes': ('collapse',)
        }),
    )
    
    def storage_size_display(self, obj):
        """
        BACKEND-READY: Display formatted storage size information.
        MAPPED TO: Admin list display
        USED BY: LibraryAdmin.list_display
        
        Shows current storage usage with tier limits for admin reference.
        """
        tier_info = {
            'basic': "Basic tier limit is 100 GB.",
            'pro': "Professional tier limit is 1 TB.",
            'enterprise': "Enterprise tier limit is 10 TB."
        }
        return f"{obj.get_storage_display()} - {tier_info.get(obj.storage_tier, '')}"
    storage_size_display.short_description = "Storage Size"
    
    def save_model(self, request, obj, form, change):
        """
        BACKEND-READY: Custom save handling for library storage tier changes.
        MAPPED TO: Admin save action
        USED BY: Django Admin save process
        
        Automatically updates storage size when tier changes.
        """
        if change and 'storage_tier' in form.changed_data:
            super().save_model(request, obj, form, change)
            obj.set_storage_size_display()
        else:
            super().save_model(request, obj, form, change)

@admin.register(UserLibraryRole)
class UserLibraryRoleAdmin(admin.ModelAdmin):
    """
    BACKEND-READY: Admin interface for managing user roles within libraries.
    MAPPED TO: /admin/libraries/userlibraryrole/
    USED BY: Django Admin panel
    
    Manages contributor and admin assignments for libraries.
    """
    list_display = ('user', 'library', 'role', 'added_at')
    list_filter = ('role', 'added_at')
    search_fields = ('user__email', 'library__name')

admin.site.register(Library, LibraryAdmin)