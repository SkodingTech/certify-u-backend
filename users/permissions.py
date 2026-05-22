from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                    hasattr(request.user, 'user_profile') and 
                    request.user.user_profile.role == 'SUPER_ADMIN')

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                    hasattr(request.user, 'user_profile') and 
                    request.user.user_profile.role in ['SUPER_ADMIN', 'ADMIN'])

class IsTeamManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                    hasattr(request.user, 'user_profile') and 
                    request.user.user_profile.role in ['SUPER_ADMIN', 'ADMIN', 'TEAM_MANAGER'])

class IsInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and
                    hasattr(request.user, 'user_profile') and
                    request.user.user_profile.role == 'INSTRUCTOR')


class IsCMSAdmin(permissions.BasePermission):
    """CMS gate — accepts Django staff/superuser OR profile role in {SUPER_ADMIN, ADMIN}."""
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_staff or user.is_superuser:
            return True
        prof = getattr(user, 'user_profile', None)
        return bool(prof and prof.role in ('SUPER_ADMIN', 'ADMIN'))

