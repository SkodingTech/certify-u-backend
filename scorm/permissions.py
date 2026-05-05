"""
SCORM Permission Classes
Custom permissions for SCORM operations
"""
from rest_framework import permissions
from users.permissions import IsAdmin, IsSuperAdmin


class IsAdminUser(permissions.BasePermission):
    """
    Allow access to SCORM admin functions (upload, manage packages)
    Only admins and superadmins
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check user role
        try:
            user_profile = request.user.userprofile
            return user_profile.role in ['ADMIN', 'SUPER_ADMIN']
        except:
            return request.user.is_staff or request.user.is_superuser


class CanAccessScormPlayer(permissions.BasePermission):
    """
    Allow access to SCORM player
    User must be authenticated and enrolled/have access
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can access this package"""
        # User can access if package is public/published
        if obj.is_active and obj.status == 'ready':
            return True

        # Or if user is instructor/admin of the package
        try:
            user_profile = request.user.userprofile
            return user_profile.role in ['ADMIN', 'SUPER_ADMIN', 'INSTRUCTOR']
        except:
            return request.user.is_staff


class CanViewTrackingData(permissions.BasePermission):
    """
    Allow viewing own tracking data or if instructor/admin
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user can view tracking data"""
        # User can view their own data
        if obj.user == request.user:
            return True

        # Instructor/admin can view any tracking
        try:
            user_profile = request.user.userprofile
            return user_profile.role in ['ADMIN', 'SUPER_ADMIN', 'INSTRUCTOR']
        except:
            return request.user.is_staff
