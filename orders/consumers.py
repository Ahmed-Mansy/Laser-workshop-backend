"""
WebSocket consumers for real-time order updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class OrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting order updates to connected clients.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get user from scope (set by AuthMiddlewareStack)
        self.user = self.scope.get('user', AnonymousUser())
        
        # Reject anonymous users
        if not self.user or self.user.is_anonymous:
            await self.close()
            return
        
        # Join the orders group
        self.group_name = 'orders'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Send confirmation message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to order updates'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the orders group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        For now, we don't process incoming messages from clients.
        """
        pass
    
    async def order_update(self, event):
        """
        Receive order update from channel layer and send to WebSocket.
        This is called when a message is sent to the group.
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'action': event.get('action'),
            'order': event.get('order')
        }))
    
    async def shift_update(self, event):
        """
        Receive shift update from channel layer and send to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'type': 'shift_update',
            'action': event.get('action'),
            'shift': event.get('shift')
        }))
