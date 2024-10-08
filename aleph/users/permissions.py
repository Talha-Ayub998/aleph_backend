from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.group == 'admin'

class IsReviewerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and not request.user.group == 'admin'
