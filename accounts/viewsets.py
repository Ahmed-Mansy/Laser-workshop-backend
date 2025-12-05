from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from orders.permissions import IsManager

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management (Manager only).
    
    - List: Get all users
    - Retrieve: Get single user
    - Update: Update user details
    - Delete: Delete user
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsManager]
    http_method_names = ['get', 'patch', 'delete']  # No POST (use register endpoint)
    
    def get_queryset(self):
        """Only return users, exclude current user from list"""
        return User.objects.exclude(id=self.request.user.id).order_by('-date_joined')
