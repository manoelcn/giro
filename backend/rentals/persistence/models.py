from decimal import Decimal

from django.db import models
from django.db.models import F, Q

from rentals.domain.enums import RentalStatus, ReservationStatus


class Reservation(models.Model):
    customer_id = models.PositiveBigIntegerField()
    vehicle_id = models.PositiveBigIntegerField()
    pickup_branch_id = models.PositiveBigIntegerField()
    return_branch_id = models.PositiveBigIntegerField()
    insurance_id = models.PositiveBigIntegerField(null=True, blank=True)
    starts_at = models.DateTimeField()
    expected_return_at = models.DateTimeField()
    status = models.CharField(
        max_length=16,
        choices=[(status.value, status.value) for status in ReservationStatus],
        default=ReservationStatus.CONFIRMED,
    )
    daily_rate_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    quoted_total = models.DecimalField(max_digits=12, decimal_places=2)
    first_day_amount_snapshot = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['vehicle_id', 'status', 'starts_at', 'expected_return_at'],
                name='rentals_res_period_idx',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(expected_return_at__gt=F('starts_at')),
                name='rentals_res_valid_period',
            ),
        ]


class Rental(models.Model):
    reservation = models.OneToOneField(
        Reservation,
        on_delete=models.PROTECT,
        related_name='rental',
    )
    status = models.CharField(
        max_length=16,
        choices=[(status.value, status.value) for status in RentalStatus],
        default=RentalStatus.RESERVED,
    )
    picked_up_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    actual_return_branch_id = models.PositiveBigIntegerField(null=True, blank=True)
    deposit_required_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    late_day_count = models.PositiveIntegerField(default=0)
    late_charge_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    inter_branch_charge_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    damage_charge_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    cancellation_charge_id = models.PositiveBigIntegerField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
