from rest_framework.permissions     import IsAuthenticated, IsAdminUser, AllowAny, BasePermission

# Check if user is superuser
# This is a custom permission class
class IsSuperUser(BasePermission):
    """
    Allows access only to super admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_superuser)


