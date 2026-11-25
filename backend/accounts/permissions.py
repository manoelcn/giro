from django.conf import settings
from rest_framework.permissions import BasePermission

from accounts.models import Employee


def _employee_for(user):
    if not user or not user.is_authenticated:
        return None
    return Employee.objects.filter(user_id=user.pk, is_active=True).first()


class _RolePermission(BasePermission):
    role = ''

    def has_permission(self, request, view):
        if settings.DEBUG:
            return True
        employee = _employee_for(request.user)
        return employee is not None and employee.role == self.role


class IsManager(_RolePermission):
    role = Employee.Role.MANAGER


class IsAttendant(_RolePermission):
    role = Employee.Role.ATTENDANT


class IsSameBranch(BasePermission):
    def has_permission(self, request, view):
        return settings.DEBUG or bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if settings.DEBUG:
            return True
        employee = _employee_for(request.user)
        object_branch_id = getattr(obj, 'branch_id', None)
        return employee is not None and object_branch_id == employee.branch_id
