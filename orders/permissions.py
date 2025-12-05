from rest_framework import permissions


class IsManager(permissions.BasePermission):
    """
    Custom permission to only allow managers to perform the action.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'MANAGER'


class IsManagerOrWorker(permissions.BasePermission):
    """
    Custom permission to allow both managers and workers.
    """
    def has_permission(request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['MANAGER', 'WORKER']
        )


class CanUpdateOrder(permissions.BasePermission):
    """
    Custom permission for order updates:
    - Managers can update all fields
    - Workers can only update status
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['MANAGER', 'WORKER']
        )
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated manager or worker
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Managers can update everything
        if request.user.role == 'MANAGER':
            return True
        
        # Workers can only update status field
        if request.user.role == 'WORKER':
            # Check if only 'status' field is being updated
            if request.method in ['PATCH', 'PUT']:
                allowed_fields = {'status'}
                update_fields = set(request.data.keys())
                return update_fields.issubset(allowed_fields)
        
        return False


class CanDeleteOrder(permissions.BasePermission):
    """
    Only managers can delete orders.
    """
    def has_permission(self, request, view):
        if request.method == 'DELETE':
            return request.user and request.user.is_authenticated and request.user.role == 'MANAGER'
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user and request.user.is_authenticated and request.user.role == 'MANAGER'
        return True
