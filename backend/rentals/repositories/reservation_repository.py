from datetime import datetime

from django.db.models import Q, QuerySet

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.models import Reservation


class ReservationRepository:
    def busy_vehicle_ids(self, starts_at: datetime, expected_return_at: datetime) -> set[int]:
        occupied = (
            Q(
                status=ReservationStatus.CONFIRMED,
                expected_return_at__gt=starts_at,
            )
            | Q(
                rental__status=RentalStatus.RESERVED,
                expected_return_at__gt=starts_at,
            )
            | Q(
                rental__status__in=[RentalStatus.PICKED_UP, RentalStatus.OVERDUE],
                rental__returned_at__isnull=True,
            )
        )
        return set(
            Reservation.objects.filter(starts_at__lt=expected_return_at)
            .filter(occupied)
            .values_list('vehicle_id', flat=True)
            .distinct()
        )

    def has_conflict(
        self,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
    ) -> bool:
        occupied = (
            Q(
                status=ReservationStatus.CONFIRMED,
                expected_return_at__gt=starts_at,
            )
            | Q(
                rental__status=RentalStatus.RESERVED,
                expected_return_at__gt=starts_at,
            )
            | Q(
                rental__status__in=[RentalStatus.PICKED_UP, RentalStatus.OVERDUE],
                rental__returned_at__isnull=True,
            )
        )
        return (
            Reservation.objects.filter(
                vehicle_id=vehicle_id,
                starts_at__lt=expected_return_at,
            )
            .filter(occupied)
            .exists()
        )

    def create(self, **values) -> Reservation:
        return Reservation.objects.create(**values)

    def get(self, reservation_id: int) -> Reservation | None:
        return (
            Reservation.objects.select_related('rental')
            .filter(pk=reservation_id)
            .first()
        )

    def list(self, **filters) -> QuerySet[Reservation]:
        return Reservation.objects.select_related('rental').filter(**filters).order_by('-created_at')
