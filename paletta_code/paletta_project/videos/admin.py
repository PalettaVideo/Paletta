from django.contrib import admin
from django.utils.html import format_html
from .models import Video, Category, Tag

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'uploader', 'upload_date', 'views_count', 'is_published')
    list_filter = ('category', 'is_published', 'upload_date')
    search_fields = ('title', 'description', 'uploader__username')
    readonly_fields = ('upload_date', 'updated_at', 'views_count', 'file_size', 'duration')
    filter_horizontal = ('tags',)
    date_hierarchy = 'upload_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'uploader', 'is_published')
        }),
        ('Media Files', {
            'fields': ('video_file', 'thumbnail')
        }),
        ('Metadata', {
            'fields': ('upload_date', 'updated_at', 'views_count', 'file_size', 'duration')
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'image_preview')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'image_preview')
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'created_at')
        }),
        ('Category Image', {
            'fields': ('image', 'image_preview'),
            'description': 'Upload an image for this category. This will be displayed on the homepage.'
        }),
    )
    
    def image_preview(self, obj):
        """Generate HTML for image preview in admin"""
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.image.url)
        return format_html('<span style="color:#999">No image</span>')
    
    image_preview.short_description = 'Image Preview'

class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

admin.site.register(Video, VideoAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)