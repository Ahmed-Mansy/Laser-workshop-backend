"""
WebSocket consumers for real-time order updates.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


class OrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting order updates to connected clients.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get user from scope (set by AuthMiddlewareStack)
        self.user = self.scope.get('user', AnonymousUser())
        
        logger.info(f"WebSocket connect attempt - User: {self.user}, Is Anonymous: {self.user.is_anonymous}")
        
        # Reject anonymous users
        if not self.user or self.user.is_anonymous:
            logger.warning("WebSocket connection rejected: Anonymous user")
            await self.close(code=4001)
            return
        
        # Join the orders group
        self.group_name = 'orders'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        logger.info(f"WebSocket connected successfully for user: {self.user.username}")
        
        # Send confirmation message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to order updates'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket disconnected - Code: {close_code}, User: {getattr(self, 'user', 'Unknown')}")
        
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
        logger.debug(f"WebSocket message received: {text_data}")
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
