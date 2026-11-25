from django.db import models


class Employee(models.Model):
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        ATTENDANT = 'ATTENDANT', 'Attendant'

    user_id = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.ATTENDANT)
    branch_id = models.PositiveBigIntegerField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name
