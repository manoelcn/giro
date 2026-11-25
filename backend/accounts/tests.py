from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory, TestCase, override_settings

from accounts.models import Employee
from accounts.permissions import IsAttendant, IsManager, IsSameBranch


class AccountPermissionsTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=True)
    def test_contract_permissions_are_open_in_development(self):
        request = self.factory.get('/')
        request.user = AnonymousUser()

        self.assertTrue(IsManager().has_permission(request, None))
        self.assertTrue(IsAttendant().has_permission(request, None))
        self.assertTrue(IsSameBranch().has_permission(request, None))

    @override_settings(DEBUG=False)
    def test_role_permissions_use_employee_record_outside_development(self):
        user = User.objects.create_user(username='manager')
        Employee.objects.create(
            user_id=user.pk,
            full_name='Gerente',
            email='manager@example.test',
            role=Employee.Role.MANAGER,
            branch_id=1,
        )
        request = self.factory.get('/')
        request.user = user

        self.assertTrue(IsManager().has_permission(request, None))
        self.assertFalse(IsAttendant().has_permission(request, None))

    @override_settings(DEBUG=False)
    def test_same_branch_permission_checks_object_branch(self):
        user = User.objects.create_user(username='attendant')
        employee = Employee.objects.create(
            user_id=user.pk,
            full_name='Atendente',
            email='attendant@example.test',
            role=Employee.Role.ATTENDANT,
            branch_id=1,
        )
        request = self.factory.get('/')
        request.user = user

        self.assertTrue(IsSameBranch().has_object_permission(request, None, employee))
        other_branch = type('BranchObject', (), {'branch_id': 2})()
        self.assertFalse(IsSameBranch().has_object_permission(request, None, other_branch))
