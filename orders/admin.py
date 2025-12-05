from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin interface for Order model"""
    list_display = ('id', 'customer_name', 'customer_phone', 'status', 'price', 'created_by', 'created_at', 'delivered_at')
    list_filter = ('status', 'created_at', 'delivered_at')
    search_fields = ('customer_name', 'customer_phone', 'order_details')
    readonly_fields = ('created_at', 'updated_at', 'delivered_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('customer_name', 'customer_phone')
        }),
        ('Order Details', {
            'fields': ('order_details', 'image', 'price')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'created_by', 'delivered_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
