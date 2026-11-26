from dataclasses import dataclass
from decimal import Decimal

from django.db import models
from django.db import transaction
from django.utils import timezone

from rentals.domain.exceptions import VehicleUnavailableException

@dataclass(frozen=True)
class RentalTerms:
    daily_rate: Decimal
    minimum_deposit: Decimal
    required_license_category: str
    minimum_age: int
    status: str


class VehicleStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    RESERVED = 'RESERVED', 'Reserved'
    RENTED = 'RENTED', 'Rented'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'


class InspectionType(models.TextChoices):
    EXIT = 'EXIT', 'Exit'
    ENTRY = 'ENTRY', 'Entry'


class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    Status = VehicleStatus

    class LicenseCategory(models.TextChoices):
        A = 'A', 'A'
        B = 'B', 'B'
        C = 'C', 'C'

    plate = models.CharField(max_length=8, unique=True)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField()
    mileage = models.PositiveIntegerField(default=0)
    last_maintenance_mileage = models.PositiveIntegerField(default=0)
    maintenance_interval_km = models.PositiveIntegerField(default=10000)
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

    def get_rental_terms(self) -> RentalTerms:
        return RentalTerms(
            daily_rate=self.daily_rate,
            minimum_deposit=self.deposit_amount,
            required_license_category=self.required_license_category,
            minimum_age=self.minimum_driver_age,
            status=self.status,
        )

    def mark_reserved(self) -> None:
        if self.status != self.Status.AVAILABLE:
            raise VehicleUnavailableException()
        self.status = self.Status.RESERVED
        self.save(update_fields=('status',))

    def mark_rented(self) -> None:
        if self.status not in (self.Status.AVAILABLE, self.Status.RESERVED):
            raise VehicleUnavailableException()
        self.status = self.Status.RENTED
        self.save(update_fields=('status',))

    def release(self) -> None:
        if self.status == self.Status.MAINTENANCE:
            Maintenance.objects.filter(
                vehicle=self,
                completed_at__isnull=True,
            ).update(completed_at=timezone.now())
            self.last_maintenance_mileage = self.mileage
        self.status = self.Status.AVAILABLE
        self.save(update_fields=('status', 'last_maintenance_mileage'))

    def send_to_maintenance(self, reason: str, mileage: int | None = None):
        maintenance_mileage = self.mileage if mileage is None else mileage
        with transaction.atomic():
            maintenance, _ = Maintenance.objects.get_or_create(
                vehicle=self,
                completed_at__isnull=True,
                defaults={
                    'reason': reason,
                    'mileage': maintenance_mileage,
                },
            )
            self.status = self.Status.MAINTENANCE
            if maintenance_mileage > self.mileage:
                self.mileage = maintenance_mileage
                self.save(update_fields=('status', 'mileage'))
            else:
                self.save(update_fields=('status',))
        return maintenance

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
    InspectionType = InspectionType

    rental_id = models.PositiveBigIntegerField()
    inspection_type = models.CharField(max_length=8, choices=InspectionType.choices)
    mileage = models.PositiveIntegerField()
    damages = models.DecimalField(max_digits=10, decimal_places=2, default='0.00')
    damage_description = models.CharField(max_length=500, blank=True)
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

    @classmethod
    def register(
        cls,
        rental_id: int,
        inspection_type: str,
        km: int,
        damages: Decimal = Decimal('0.00'),
        damage_description: str = '',
    ):
        with transaction.atomic():
            inspection = cls.objects.create(
                rental_id=rental_id,
                inspection_type=inspection_type,
                mileage=km,
                damages=damages,
                damage_description=damage_description,
            )
            from rentals.models import Rental

            rental = Rental.objects.select_related('reservation').filter(pk=rental_id).first()
            if rental is None:
                return inspection

            vehicle = Vehicle.objects.select_for_update().get(
                pk=rental.reservation.vehicle_id,
            )
            vehicle.mileage = max(vehicle.mileage, km)
            vehicle.save(update_fields=('mileage',))

            if inspection_type == cls.InspectionType.ENTRY:
                if damages > 0:
                    vehicle.send_to_maintenance(
                        reason=damage_description or 'Avaria identificada na vistoria',
                        mileage=km,
                    )
                elif km - vehicle.last_maintenance_mileage >= vehicle.maintenance_interval_km:
                    vehicle.send_to_maintenance(
                        reason='Revisão por quilometragem',
                        mileage=km,
                    )
            return inspection

    @property
    def has_damage(self) -> bool:
        return self.damages > 0


class Maintenance(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='maintenances')
    reason = models.CharField(max_length=255)
    mileage = models.PositiveIntegerField()
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('vehicle',),
                condition=models.Q(completed_at__isnull=True),
                name='fleet_unique_active_maintenance',
            ),
        ]

    def __str__(self):
        return f'{self.vehicle.plate} - {self.reason}'
