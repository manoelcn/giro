from django.db import models


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        BLOCKED = 'BLOCKED', 'Blocked'

    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    birth_date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    completed_rentals = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.full_name


class DriverLicense(models.Model):
    class Category(models.TextChoices):
        A = 'A', 'A'
        B = 'B', 'B'
        AB = 'AB', 'AB'
        C = 'C', 'C'
        D = 'D', 'D'
        E = 'E', 'E'

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='licenses')
    number = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=2, choices=Category.choices)
    expires_on = models.DateField()

    def __str__(self):
        return f'{self.number} ({self.category})'


class Insurance(models.Model):
    name = models.CharField(max_length=100, unique=True)
    daily_cost = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    deductible = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    coverage_limit = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')

    def __str__(self):
        return self.name

    def calculate_daily_cost(self):
        return self.daily_cost

    def calculate_customer_damage_cost(self, damage_value):
        return min(damage_value, self.deductible)


class BasicInsurance(Insurance):
    pass


class FullInsurance(Insurance):
    third_party_coverage = models.BooleanField(default=False)
    roadside_assistance = models.BooleanField(default=False)
