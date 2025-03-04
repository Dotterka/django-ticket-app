from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow only superusers to access the view.
    """
    def has_permission(self, request, view):
        # Allow GET requests for everyone (authenticated)
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_superuser