from django.contrib import admin
from .models import Order, OrderDetail, DownloadRequest

class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ('added_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'library', 'total_price', 'order_date', 'payment_status')
    list_filter = ('payment_status', 'order_date', 'library')
    search_fields = ('user__email', 'id')
    readonly_fields = ('order_date',)
    inlines = [OrderDetailInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'library')

@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'video', 'resolution', 'price', 'download_status')
    list_filter = ('download_status', 'resolution', 'added_at')
    search_fields = ('video__title', 'order__id')
    readonly_fields = ('added_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order', 'video')

@admin.register(DownloadRequest)
class DownloadRequestAdmin(admin.ModelAdmin):
    """
    BACKEND-READY: Admin interface for download request management.
    MAPPED TO: Django admin /admin/orders/downloadrequest/
    USED BY: Admin staff for monitoring download requests and troubleshooting
    
    Provides filtering, search, and bulk actions for download request management.
    Shows request status, expiry tracking, and email delivery status.
    """
    
    list_display = (
        'id', 'user', 'video_title', 'email', 'status', 
        'request_date', 'expiry_date', 'email_sent', 'is_expired_display'
    )
    list_filter = (
        'status', 'email_sent', 'request_date', 'expiry_date',
        'video__library'
    )
    search_fields = (
        'user__email', 'email', 'video__title', 
        's3_key', 'aws_request_id'
    )
    readonly_fields = (
        'request_date', 'email_sent_at', 'expiry_date', 
        'is_expired_display', 'aws_request_id'
    )
    
    date_hierarchy = 'request_date'
    ordering = ['-request_date']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'video', 'email', 'status')
        }),
        ('Download Details', {
            'fields': ('download_url', 's3_key', 'expiry_date', 'is_expired_display')
        }),
        ('Email Tracking', {
            'fields': ('email_sent', 'email_sent_at', 'email_error')
        }),
        ('AWS Metadata', {
            'fields': ('aws_request_id',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('request_date',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_expired', 'resend_email', 'mark_as_completed']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'video', 'video__library')
    
    def video_title(self, obj):
        """Display video title with library information."""
        return f"{obj.video.title} ({obj.video.library.name})"
    video_title.short_description = "Video"
    video_title.admin_order_field = 'video__title'
    
    def is_expired_display(self, obj):
        """Display expiry status with visual indicator."""
        expired = obj.is_expired()
        if expired:
            return "Expired"
        else:
            return "Valid"
    is_expired_display.short_description = "Expiry Status"
    is_expired_display.boolean = False
    
    def mark_as_expired(self, request, queryset):
        """Bulk action to mark selected requests as expired."""
        updated = 0
        for obj in queryset:
            if obj.mark_expired():
                updated += 1
        
        self.message_user(
            request,
            f"Successfully marked {updated} download requests as expired."
        )
    mark_as_expired.short_description = "Mark selected requests as expired"
    
    def resend_email(self, request, queryset):
        """Bulk action to resend emails for selected requests."""
        # This will be implemented when we create the email service
        self.message_user(
            request,
            "Email resend functionality will be available after implementing the email service."
        )
    resend_email.short_description = "Resend download emails"
    
    def mark_as_completed(self, request, queryset):
        """Bulk action to mark selected requests as completed."""
        updated = queryset.update(status='completed')
        self.message_user(
            request,
            f"Successfully marked {updated} download requests as completed."
        )
    mark_as_completed.short_description = "Mark selected requests as completed" 