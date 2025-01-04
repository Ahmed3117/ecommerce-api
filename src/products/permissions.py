from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow users to manage their own ratings
        return obj.user == request.user
