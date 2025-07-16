from django.contrib import admin
from django.utils.html import format_html
from .models import Video, Tag, VideoLog, VideoTag, ContentType, PalettaContentType
from django.urls import reverse

class VideoLogInline(admin.TabularInline):
    """
    BACKEND-READY: Inline admin interface for VideoLog model.
    MAPPED TO: Django admin video detail pages
    USED BY: Admin users viewing video activity logs
    
    Displays video activity logs within video detail admin page.
    Read-only interface with styled log types and formatted file sizes.
    """
    model = VideoLog
    extra = 0
    readonly_fields = ('log_type_display', 'timestamp', 'user_username', 'message', 'storage_status', 'file_size_display')
    fields = ('log_type_display', 'timestamp', 'user_username', 'message', 'storage_status', 'file_size_display')
    can_delete = False
    max_num = 0  # Don't allow adding new logs
    
    def log_type_display(self, obj):
        """
        BACKEND-READY: Display log type with color-coded styling.
        MAPPED TO: Django admin log display
        USED BY: Admin interface for visual log type identification
        
        Applies color coding to different log types for better readability.
        Required fields: obj.log_type
        """
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
    """
    BACKEND-READY: Comprehensive admin interface for Video model.
    MAPPED TO: Django admin /admin/videos/video/
    USED BY: Admin users for video management and monitoring
    
    Provides video listing, editing, and monitoring with S3 status tracking.
    Includes file size formatting, duration display, and activity logging.
    """
    search_fields = ('title', 'description', 'uploader__username')
    ordering = ('-upload_date',)
    list_display = ('title', 'uploader', 'content_type', 'library', 'upload_date', 'file_size_display', 'duration_display', 'views_count', 'storage_status_display')
    list_filter = ('content_type', 'library', 'upload_date', 'storage_status')
    readonly_fields = ('upload_date', 'updated_at', 'views_count', 'file_size', 'duration', 'storage_status', 'storage_url', 'storage_reference_id', 'display_content_types')
    date_hierarchy = 'upload_date'
    inlines = [VideoLogInline, VideoTagInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'content_type', 'library')
        }),
        ('Content Types Summary', {
            'fields': ('display_content_types',),
            'classes': ('collapse',)
        }),
        ('File Information', {
            'fields': ('video_file', 'thumbnail', 'file_size', 'duration', 'views_count')
        }),
        ('Storage Information', {
            'fields': ('storage_status', 'storage_url', 'storage_reference_id', 'download_link', 'download_link_expiry')
        }),
    )
    
    def content_type_display(self, obj):
        """Display the content type"""
        if obj.content_type:
            return obj.content_type.display_name
        return '-'
    content_type_display.short_description = 'Content Type'
    
    def storage_status_display(self, obj):
        """
        BACKEND-READY: Display storage status with color-coded styling.
        MAPPED TO: Django admin video list view
        USED BY: Admin interface for visual status identification
        
        Applies color coding to storage statuses for quick visual assessment.
        Required fields: obj.storage_status
        """
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
        """
        BACKEND-READY: Display file size in human-readable format.
        MAPPED TO: Django admin file size display
        USED BY: Admin interface for storage monitoring
        
        Converts bytes to appropriate units (B, KB, MB, GB, TB).
        Required fields: obj.file_size
        """
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

class ContentTypeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'subject_area', 'custom_name', 'library', 'is_active')
    list_filter = ('is_active', 'library', 'subject_area')
    search_fields = ('subject_area', 'custom_name', 'library__name')
    readonly_fields = ('display_name',)
    
    fieldsets = (
        ('Content Type Information', {
            'fields': ('subject_area', 'custom_name', 'display_name', 'library', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('description', 'image'),
            'classes': ('collapse',)
        }),
    )

class PalettaContentTypeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'description')
    readonly_fields = ('display_name',)
    
    fieldsets = (
        ('Paletta Content Type Information', {
            'fields': ('code', 'display_name', 'description', 'is_active')
        }),
    )

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'library')
    list_filter = ('library',)
    search_fields = ('name',)

class VideoTagAdmin(admin.ModelAdmin):
    list_display = ('video', 'tag')
    list_filter = ('tag',)
    search_fields = ('video__title', 'tag__name')

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

# Register the models with admin
admin.site.register(Video, VideoAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(PalettaContentType, PalettaContentTypeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(VideoTag, VideoTagAdmin)

admin.site.register(VideoLog, VideoLogAdmin)