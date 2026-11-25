from datetime import datetime

from rentals.repositories.reservation_repository import ReservationRepository


class ReservationQuery:
    def __init__(self, repository: ReservationRepository | None = None) -> None:
        self.repository = repository or ReservationRepository()

    def busy_vehicle_ids(self, starts_at: datetime, expected_return_at: datetime) -> set[int]:
        return self.repository.busy_vehicle_ids(starts_at, expected_return_at)
