from django.db import models
from django.utils import timezone
from accounts.models import User
from videos.models import Video
from libraries.models import Library

class Order(models.Model):
    """Model representing a customer order with video downloads."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='orders')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order_date = models.DateTimeField(default=timezone.now)
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.email} - {self.order_date.strftime('%Y-%m-%d')}"
    
    def calculate_total(self):
        """Calculate and update the total price based on order details."""
        total = sum(detail.price for detail in self.details.all())
        self.total_price = total
        self.save(update_fields=['total_price'])
        return total


class OrderDetail(models.Model):
    """Model representing individual videos in an order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='details')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='order_details')
    resolution = models.CharField(max_length=20, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)
    
    DOWNLOAD_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    download_status = models.CharField(
        max_length=20, 
        choices=DOWNLOAD_STATUS_CHOICES,
        default='pending'
    )
    
    # Track the download URL and expiration
    download_url = models.URLField(max_length=500, blank=True, null=True)
    download_url_expiry = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.video.title} in Order #{self.order.id}"
    
    class Meta:
        unique_together = ('order', 'video', 'resolution')


class DownloadRequest(models.Model):
    """
    BACKEND-READY: Model for tracking individual video download requests.
    MAPPED TO: Download request system
    USED BY: Download request API, email automation, cleanup tasks
    
    Tracks download requests with 48-hour expiry, presigned S3 URLs, and email status.
    Separate from OrderDetail to allow tracking of individual download requests.
    Required fields: user, video, email, expiry_date
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_requests')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='download_requests')
    email = models.EmailField(help_text="Email address to send download link to")
    
    # Request tracking
    request_date = models.DateTimeField(default=timezone.now)
    
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),        # Request created, awaiting processing
        ('completed', 'Completed'),    # Email sent successfully
        ('failed', 'Failed'),          # S3 or email error occurred
        ('expired', 'Expired'),        # 48-hour period has passed
    ]
    status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS_CHOICES,
        default='pending',
        help_text="Status of the download request"
    )
    
    # S3 presigned URL tracking
    download_url = models.URLField(max_length=500, blank=True, null=True, help_text="S3 presigned URL for download")
    expiry_date = models.DateTimeField(help_text="When the download link expires (48 hours from creation)")
    
    # Email tracking
    email_sent = models.BooleanField(default=False, help_text="Whether the email has been sent")
    email_sent_at = models.DateTimeField(blank=True, null=True, help_text="When the email was sent")
    email_error = models.TextField(blank=True, help_text="Any error messages from email sending")
    
    # Metadata for AWS integration
    s3_key = models.CharField(max_length=500, blank=True, help_text="S3 key for the video file")
    aws_request_id = models.CharField(max_length=100, blank=True, help_text="AWS request ID for tracking")
    
    class Meta:
        ordering = ['-request_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Download request for '{self.video.title}' by {self.user.email} - {self.get_status_display()}"
    
    def is_expired(self):
        """Check if this download request has expired."""
        return timezone.now() > self.expiry_date
    
    def mark_expired(self):
        """Mark this request as expired if it has passed expiry time."""
        if self.is_expired() and self.status not in ['expired']:
            self.status = 'expired'
            self.save(update_fields=['status'])
            return True
        return False
    
    def generate_expiry_date(self):
        """Generate expiry date 48 hours from now."""
        return timezone.now() + timezone.timedelta(seconds=172800)  # 48 hours
    
    def save(self, *args, **kwargs):
        """Auto-set expiry date on creation if not provided."""
        if not self.expiry_date:
            self.expiry_date = self.generate_expiry_date()
        super().save(*args, **kwargs) 