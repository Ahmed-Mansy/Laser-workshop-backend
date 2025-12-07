"""
Custom middleware for JWT authentication on WebSocket connections.
"""
import logging
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()
logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Get user from JWT access token.
    """
    try:
        # Decode and validate token
        access_token = AccessToken(token_string)
        user_id = access_token['user_id']
        
        # Get user from database
        user = User.objects.get(id=user_id)
        logger.info(f"WebSocket auth successful for user: {user.username} (ID: {user.id})")
        return user
    except Exception as e:
        logger.error(f"WebSocket auth error: {type(e).__name__}: {str(e)}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens.
    Token should be passed as a query parameter: ?token=<jwt_token>
    """
    
    async def __call__(self, scope, receive, send):
        # Get query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        
        # Extract token from query params
        token = query_params.get('token', [None])[0]
        
        if token:
            logger.info("WebSocket connection attempt with token")
            # Get user from token
            scope['user'] = await get_user_from_token(token)
        else:
            logger.warning("WebSocket connection attempt without token")
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
