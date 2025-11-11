from rest_framework.permissions import BasePermission

class IsCourier(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'courier')