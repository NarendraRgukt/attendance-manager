from rest_framework import permissions
from roles.models import Member


class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            try:
                member=Member.objects.filter(user=request.user,role__name="admin").exists()
                return member
            except Member.DoesNotExist:
                return False
        return False
