from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    Extends Django's AbstractUser to add role field for Manager/Worker distinction.
    """
    
    ROLE_CHOICES = (
        ('MANAGER', 'Manager'),
        ('WORKER', 'Worker'),
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='WORKER',
        help_text='User role determines access level in the system'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_manager(self):
        """Check if user is a manager"""
        return self.role == 'MANAGER'
    
    @property
    def is_worker(self):
        """Check if user is a worker"""
        return self.role == 'WORKER'
