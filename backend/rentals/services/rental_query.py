from datetime import datetime

from django.db.models import QuerySet

from rentals.domain.enums import RentalStatus
from rentals.models import Rental
from rentals.repositories.rental_repository import RentalRepository


class RentalQuery:
    def __init__(self, repository: RentalRepository | None = None) -> None:
        self.repository = repository or RentalRepository()

    def list_by_customer(self, customer_id: int) -> QuerySet[Rental]:
        return self.repository.list().filter(reservation__customer_id=customer_id)

    def list_overdue(self) -> QuerySet[Rental]:
        return self.repository.list().filter(status=RentalStatus.OVERDUE)

    def list_by_period(
        self,
        branch_id: int | None,
        start: datetime,
        end: datetime,
    ) -> QuerySet[Rental]:
        rentals = self.repository.list().filter(
            reservation__starts_at__lt=end,
            reservation__expected_return_at__gt=start,
        )
        if branch_id is not None:
            rentals = rentals.filter(reservation__pickup_branch_id=branch_id)
        return rentals

    def list(
        self,
        *,
        customer_id: int | None = None,
        status: str | None = None,
        pickup_branch_id: int | None = None,
        starts_at: datetime | None = None,
        expected_return_at: datetime | None = None,
    ) -> QuerySet[Rental]:
        rentals = self.repository.list()
        if customer_id is not None:
            rentals = rentals.filter(reservation__customer_id=customer_id)
        if status is not None:
            rentals = rentals.filter(status=status)
        if pickup_branch_id is not None:
            rentals = rentals.filter(reservation__pickup_branch_id=pickup_branch_id)
        if starts_at is not None:
            rentals = rentals.filter(reservation__expected_return_at__gt=starts_at)
        if expected_return_at is not None:
            rentals = rentals.filter(reservation__starts_at__lt=expected_return_at)
        return rentals
