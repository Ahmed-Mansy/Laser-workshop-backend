from rest_framework import serializers
from django.utils import timezone
from .models import Order, Shift


class ShiftSerializer(serializers.ModelSerializer):
    """Serializer for Shift model with real-time stats"""
    duration_hours = serializers.SerializerMethodField()
    opened_by_username = serializers.CharField(source='opened_by.username', read_only=True)
    closed_by_username = serializers.CharField(source='closed_by.username', read_only=True)
    total_orders_delivered = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'opened_at', 'closed_at', 'is_active',
            'total_orders_delivered', 'total_revenue', 'duration_hours',
            'opened_by', 'opened_by_username', 'closed_by', 'closed_by_username'
        ]
        read_only_fields = [
            'id', 'opened_at', 'opened_by', 'closed_by'
        ]
    
    def get_duration_hours(self, obj):
        """Calculate shift duration in hours"""
        if obj.closed_at:
           delta = obj.closed_at - obj.opened_at
        else:
            delta = timezone.now() - obj.opened_at
        return round(delta.total_seconds() / 3600, 2)
    
    def get_total_orders_delivered(self, obj):
        """Get real-time count of delivered orders in this shift"""
        from .models import Order
        from django.db.models import Q
        
        if obj.is_active:
            # For active shifts, count orders delivered since shift opened
            return Order.objects.filter(
                status='DELIVERED',
                delivered_at__gte=obj.opened_at,
                delivered_at__isnull=False
            ).count()
        else:
            # For closed shifts, use stored value
            return obj.total_orders_delivered
    
    def get_total_revenue(self, obj):
        """Get real-time revenue from delivered orders in this shift"""
        from .models import Order
        from django.db.models import Sum
        
        if obj.is_active:
            # For active shifts, calculate revenue from orders delivered since shift opened
            revenue = Order.objects.filter(
                status='DELIVERED',
                delivered_at__gte=obj.opened_at,
                delivered_at__isnull=False
            ).aggregate(Sum('price'))['price__sum']
            return float(revenue) if revenue else 0.0
        else:
            # For closed shifts, use stored value
            return float(obj.total_revenue)


class OrderSerializer(serializers.ModelSerializer):
    """Full serializer for Order model"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'customer_name', 'customer_phone', 'order_details', 'image',
            'price', 'status', 'status_display', 'created_by', 'created_by_username',
            'created_at', 'updated_at', 'delivered_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'delivered_at', 'created_by')
    
    def validate(self, attrs):
        # Validate that price is set when status is DELIVERED
        status = attrs.get('status', self.instance.status if self.instance else None)
        price = attrs.get('price', self.instance.price if self.instance else None)
        
        if status == 'DELIVERED' and not price:
            raise serializers.ValidationError({
                'price': 'Price is required when order is marked as delivered.'
            })
        
        return attrs


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new orders (workers use this)"""
    
    class Meta:
        model = Order
        fields = ('customer_name', 'customer_phone', 'order_details', 'image', 'price', 'status')
        extra_kwargs = {
            'status': {'default': 'UNDER_WORK'}
        }


class OrderUpdateStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating order status (used by workers)"""
    
    class Meta:
        model = Order
        fields = ['status']
    
    def update(self, instance, validated_data):
        """Update the order and set delivered_at when status changes to DELIVERED"""
        new_status = validated_data.get('status')
        
        # Set delivered_at timestamp when order is marked as DELIVERED
        if new_status == 'DELIVERED' and instance.status != 'DELIVERED':
            instance.delivered_at = timezone.now()
        
        instance.status = new_status
        instance.save()
        return instance


class OrderShowcaseSerializer(serializers.ModelSerializer):
    """Serializer for public showcase (limited fields)"""
    
    class Meta:
        model = Order
        fields = ('id', 'customer_name', 'image', 'order_details', 'delivered_at')
