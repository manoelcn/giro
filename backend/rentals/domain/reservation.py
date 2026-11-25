from dataclasses import dataclass
from datetime import datetime

from rentals.domain.enums import ReservationStatus
from rentals.domain.exceptions import InvalidStateTransitionException


@dataclass
class Reservation:
    customer_id: int
    vehicle_id: int
    starts_at: datetime
    expected_return_at: datetime
    status: ReservationStatus = ReservationStatus.CONFIRMED

    def transition_to(self, new_status: ReservationStatus) -> None:
        allowed_transitions = {
            ReservationStatus.CONFIRMED: {
                ReservationStatus.CANCELED,
                ReservationStatus.FULFILLED,
            },
            ReservationStatus.CANCELED: set(),
            ReservationStatus.FULFILLED: set(),
        }
        if new_status not in allowed_transitions[self.status]:
            raise InvalidStateTransitionException()
        self.status = new_status
