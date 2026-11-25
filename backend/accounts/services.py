from django.conf import settings

from accounts.models import Employee


class AccountAccess:
    def can_operate_in_branch(self, actor_id: int, branch_id: int) -> bool:
        if settings.DEBUG:
            return True
        return Employee.objects.filter(
            user_id=actor_id,
            branch_id=branch_id,
            is_active=True,
        ).exists()
