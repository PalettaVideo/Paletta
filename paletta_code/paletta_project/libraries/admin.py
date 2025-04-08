from django.contrib import admin
from django.forms import ModelForm
from .models import Library, UserLibraryRole

class LibraryAdminForm(ModelForm):
    class Meta:
        model = Library
        fields = '__all__'

class LibraryAdmin(admin.ModelAdmin):
    form = LibraryAdminForm
    list_display = ('name', 'owner', 'created_at', 'storage_tier', 'get_storage_display', 'is_active')
    list_filter = ['owner', 'storage_tier', 'is_active']
    search_fields = ('name', 'description')
    readonly_fields = ('storage_size_display',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner', 'logo', 'is_active')
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
        """Display the current storage size."""
        tier_info = {
            'basic': f"Basic tier limit is 100 GB.",
            'pro': f"Professional tier limit is 1 TB.",
            'enterprise': f"Enterprise tier limit is 10 TB."
        }
        return f"{obj.get_storage_display()} - {tier_info.get(obj.storage_tier, '')}"
    storage_size_display.short_description = "Storage Size"
    
    def save_model(self, request, obj, form, change):
        """
        When saving a library, automatically update the storage size if tier changed.
        """
        if change and 'storage_tier' in form.changed_data:
            # First save the model with the new tier
            super().save_model(request, obj, form, change)
            # Then update the storage size based on the new tier
            obj.set_storage_size_display()
        else:
            # Normal save otherwise
            super().save_model(request, obj, form, change)

@admin.register(UserLibraryRole)
class UserLibraryRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'library', 'role', 'added_at')
    list_filter = ('role', 'added_at')
    search_fields = ('user__username', 'library__name')

admin.site.register(Library, LibraryAdmin)