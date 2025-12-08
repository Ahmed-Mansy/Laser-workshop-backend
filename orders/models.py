from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class Shift(models.Model):
    """
    Represents a work shift for tracking daily operations.
    Managers can open/close shifts to track delivered orders and revenue.
    """
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opened_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='opened_shifts'
    )
    closed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_shifts'
    )
    is_active = models.BooleanField(default=True)
    
    # Statistics (calculated when shift closes)
    total_orders_delivered = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        ordering = ['-opened_at']
    
    def __str__(self):
        status = "Active" if self.is_active else "Closed"
        return f"Shift {self.id} - {status} ({self.opened_at.strftime('%Y-%m-%d %H:%M')})"



class Order(models.Model):
    """
    Order model representing a laser workshop order with workflow stages.
    Tracks customer information, order details, pricing, and status progression.
   """
    
    STATUS_CHOICES = (
        ('UNDER_WORK', 'Under Work'),
        ('DESIGNING', 'Designing'),
        ('DESIGN_COMPLETED', 'Design Completed'),
        ('DONE_CUTTING', 'Done Cutting'),
        ('DELIVERED', 'Delivered'),
    )
    
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15)
    order_details = models.TextField(help_text='Description of the order')
    image = models.ImageField(
        upload_to='orders/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Optional image of the order'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Order price (required when delivered)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UNDER_WORK',
        help_text='Current status in the workflow'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date and time when order was delivered'
    )
    delivered_in_shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivered_orders',
        help_text='Shift during which this order was delivered'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['delivered_at']),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer_name} ({self.get_status_display()})"
    
    def clean(self):
        """Validate that price is set when status is DELIVERED"""
        if self.status == 'DELIVERED' and not self.price:
            raise ValidationError({
                'price': 'Price is required when order is marked as delivered.'
            })
    
    def save(self, *args, **kwargs):
        # Automatically set delivered_at when status changes to DELIVERED
        if self.status == 'DELIVERED' and not self.delivered_at:
            self.delivered_at = timezone.now()
        
        # Reset delivered_at if status changes from DELIVERED to something else
        if self.status != 'DELIVERED' and self.delivered_at:
            self.delivered_at = None
        
        self.full_clean()
        super().save(*args, **kwargs)
