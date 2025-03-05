from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow only superusers to edit, create or delete.
    """
    def has_permission(self, request, view):
        # Allow GET requests for everyone
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_superuser
    
class IsAdminOrOwner(BasePermission):
    """
    Custom permission to allow only admins and owners to access an order.
    """

    def has_object_permission(self, request, view, obj):
        return request.user and (request.user.is_staff or obj.user == request.user)
    
class OnlyGetMethod(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET']:
            return True
        return False
    
class DisableMethodsPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['PUT', 'PATCH']:
            return False
        return True