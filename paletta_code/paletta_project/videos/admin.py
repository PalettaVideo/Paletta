from django.contrib import admin
from django.utils.html import format_html
from .models import Video, Category, Tag, VideoLog, VideoTag, Upload
from django.urls import reverse

class VideoLogInline(admin.TabularInline):
    """Inline admin interface for VideoLog model."""
    model = VideoLog
    extra = 0
    readonly_fields = ('log_type_display', 'timestamp', 'user_username', 'message', 'storage_status', 'file_size_display')
    fields = ('log_type_display', 'timestamp', 'user_username', 'message', 'storage_status', 'file_size_display')
    can_delete = False
    max_num = 0  # Don't allow adding new logs
    
    def log_type_display(self, obj):
        """Display the log type with appropriate styling."""
        log_type_colors = {
            'upload': 'blue',
            'process': 'orange',
            'store': 'green',
            'download': 'purple',
            'delete': 'red',
            'error': 'red',
            'status_change': 'teal',
        }
        color = log_type_colors.get(obj.log_type, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_log_type_display())
    log_type_display.short_description = 'Log Type'
    
    def user_username(self, obj):
        """Display the username with a link to the user admin page."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_username.short_description = 'User'
    
    def file_size_display(self, obj):
        """Display the file size in a human-readable format."""
        if obj.file_size:
            # Convert bytes to appropriate unit
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size = obj.file_size
            unit_index = 0
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            return f"{size:.2f} {units[unit_index]}"
        return '-'
    file_size_display.short_description = 'File Size'

class VideoTagInline(admin.TabularInline):
    model = VideoTag
    extra = 1
    autocomplete_fields = ['tag']

class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'category', 'library', 'upload_date', 'storage_status_display', 'file_size_display', 'duration_display', 'views_count', 'is_published')
    list_filter = ('category', 'library', 'upload_date', 'is_published', 'storage_status')
    search_fields = ('title', 'description', 'uploader__username')
    readonly_fields = ('upload_date', 'updated_at', 'views_count', 'file_size', 'duration', 'storage_status', 'storage_url', 'storage_reference_id')
    date_hierarchy = 'upload_date'
    inlines = [VideoLogInline, VideoTagInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'library', 'is_published')
        }),
        ('Upload Information', {
            'fields': ('uploader', 'upload_date', 'updated_at', 'views_count')
        }),
        ('File Information', {
            'fields': ('video_file', 'thumbnail', 'file_size', 'duration')
        }),
        ('Storage Information', {
            'fields': ('storage_status', 'storage_url', 'storage_reference_id', 'download_link', 'download_link_expiry')
        }),
    )
    
    def storage_status_display(self, obj):
        """Display the storage status with appropriate styling."""
        status_colors = {
            'pending': 'orange',
            'uploading': 'blue',
            'stored': 'green',
            'failed': 'red',
            'processing': 'purple',
        }
        color = status_colors.get(obj.storage_status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_storage_status_display())
    storage_status_display.short_description = 'Storage Status'
    
    def file_size_display(self, obj):
        """Display the file size in a human-readable format."""
        if obj.file_size:
            # Convert bytes to appropriate unit
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size = obj.file_size
            unit_index = 0
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            return f"{size:.2f} {units[unit_index]}"
        return '-'
    file_size_display.short_description = 'File Size'
    
    def duration_display(self, obj):
        """Display the duration in a human-readable format."""
        if obj.duration:
            minutes, seconds = divmod(obj.duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            else:
                return f"{minutes}m {seconds}s"
        return '-'
    duration_display.short_description = 'Duration'

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'library', 'description', 'created_at', 'image_preview')
    list_filter = ('library',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'image_preview')
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'library', 'created_at')
        }),
        ('Category Image', {
            'fields': ('image', 'image_preview'),
            'description': 'Upload an image for this category. This will be displayed on the homepage.'
        }),
    )
    
    def image_preview(self, obj):
        """Display a preview of the category image."""
        if obj.image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image Preview'

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'library')
    list_filter = ('library',)
    search_fields = ('name',)

class VideoTagAdmin(admin.ModelAdmin):
    list_display = ('video', 'tag')
    list_filter = ('tag',)
    search_fields = ('video__title', 'tag__name')

class UploadAdmin(admin.ModelAdmin):
    list_display = ('video', 'uploader', 'upload_date', 'status')
    list_filter = ('status', 'upload_date')
    search_fields = ('video__title', 'uploader__username')
    readonly_fields = ('upload_date',)
    date_hierarchy = 'upload_date'

class VideoLogAdmin(admin.ModelAdmin):
    """Admin interface for VideoLog model."""
    list_display = ('log_type_display', 'video_title', 'user_username', 'timestamp', 'storage_status', 'file_size_display', 'ip_address')
    list_filter = ('log_type', 'timestamp', 'storage_status')
    search_fields = ('video__title', 'user__username', 'message', 'ip_address')
    readonly_fields = ('video', 'user', 'timestamp', 'log_type', 'message', 'ip_address', 'user_agent', 'file_size', 'storage_status', 'duration')
    date_hierarchy = 'timestamp'
    
    def log_type_display(self, obj):
        """Display the log type with appropriate styling."""
        log_type_colors = {
            'upload': 'blue',
            'process': 'orange',
            'store': 'green',
            'download': 'purple',
            'delete': 'red',
            'error': 'red',
            'status_change': 'teal',
        }
        color = log_type_colors.get(obj.log_type, 'black')
        return format_html('<span style="color: {};">{}</span>', color, obj.get_log_type_display())
    log_type_display.short_description = 'Log Type'
    
    def video_title(self, obj):
        """Display the video title with a link to the video admin page."""
        if obj.video:
            url = reverse('admin:videos_video_change', args=[obj.video.id])
            return format_html('<a href="{}">{}</a>', url, obj.video.title)
        return '-'
    video_title.short_description = 'Video'
    
    def user_username(self, obj):
        """Display the username with a link to the user admin page."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_username.short_description = 'User'
    
    def file_size_display(self, obj):
        """Display the file size in a human-readable format."""
        if obj.file_size:
            # Convert bytes to appropriate unit
            units = ['B', 'KB', 'MB', 'GB', 'TB']
            size = obj.file_size
            unit_index = 0
            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1
            return f"{size:.2f} {units[unit_index]}"
        return '-'
    file_size_display.short_description = 'File Size'

# Register the models with the admin site
admin.site.register(Video, VideoAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(VideoTag, VideoTagAdmin)
admin.site.register(Upload, UploadAdmin)
admin.site.register(VideoLog, VideoLogAdmin)