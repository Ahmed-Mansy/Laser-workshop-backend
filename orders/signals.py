"""
Django signals for broadcasting order and shift changes via WebSocket.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Order, Shift
from .serializers import OrderSerializer, ShiftSerializer


@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    """
    Broadcast order creation/update to all connected WebSocket clients.
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_update',
                'action': 'created' if created else 'updated',
                'order': OrderSerializer(instance).data
            }
        )


@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    """
    Broadcast order deletion to all connected WebSocket clients.
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_update',
                'action': 'deleted',
                'order': {'id': instance.id}
            }
        )


@receiver(post_save, sender=Shift)
def shift_saved(sender, instance, created, **kwargs):
    """
    Broadcast shift creation/update to all connected WebSocket clients.
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'shift_update',
                'action': 'created' if created else 'updated',
                'shift': ShiftSerializer(instance).data
            }
        )
