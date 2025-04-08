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