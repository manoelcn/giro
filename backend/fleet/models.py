from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        RESERVED = 'RESERVED', 'Reserved'
        RENTED = 'RENTED', 'Rented'
        MAINTENANCE = 'MAINTENANCE', 'Maintenance'

    class LicenseCategory(models.TextChoices):
        A = 'A', 'A'
        B = 'B', 'B'
        C = 'C', 'C'

    plate = models.CharField(max_length=8, unique=True)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    mileage = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default='120.00')
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default='300.00')
    required_license_category = models.CharField(
        max_length=1,
        choices=LicenseCategory.choices,
        default=LicenseCategory.B,
    )
    minimum_driver_age = models.PositiveSmallIntegerField(default=21)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='vehicles')

    def __str__(self):
        return f'{self.plate} - {self.model}'

    @property
    def vehicle_type(self):
        for relation in ('car', 'motorcycle', 'utilityvehicle'):
            try:
                getattr(self, relation)
            except Vehicle.DoesNotExist:
                continue
            return relation.upper()
        return 'VEHICLE'


class Car(Vehicle):
    doors = models.PositiveSmallIntegerField(default=4)
    trunk_capacity_liters = models.PositiveSmallIntegerField(default=300)


class Motorcycle(Vehicle):
    displacement_cc = models.PositiveSmallIntegerField(default=150)
    helmet_included = models.BooleanField(default=True)


class UtilityVehicle(Vehicle):
    load_capacity_kg = models.PositiveSmallIntegerField(default=500)


class Inspection(models.Model):
    class InspectionType(models.TextChoices):
        EXIT = 'EXIT', 'Exit'
        ENTRY = 'ENTRY', 'Entry'

    rental_id = models.PositiveBigIntegerField()
    inspection_type = models.CharField(max_length=8, choices=InspectionType.choices)
    mileage = models.PositiveIntegerField()
    damages = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('rental_id', 'inspection_type'),
                name='fleet_unique_rental_inspection_type',
            )
        ]

    def __str__(self):
        return f'{self.rental_id} - {self.inspection_type}'
