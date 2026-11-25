from dataclasses import dataclass

from rentals.domain.enums import RentalStatus
from rentals.domain.exceptions import InvalidStateTransitionException


@dataclass
class Rental:
    reservation_id: int
    status: RentalStatus = RentalStatus.RESERVED

    def transition_to(self, new_status: RentalStatus) -> None:
        allowed_transitions = {
            RentalStatus.RESERVED: {RentalStatus.PICKED_UP, RentalStatus.CANCELED},
            RentalStatus.PICKED_UP: {RentalStatus.OVERDUE, RentalStatus.RETURNED},
            RentalStatus.OVERDUE: {RentalStatus.RETURNED},
            RentalStatus.RETURNED: {RentalStatus.COMPLETED},
            RentalStatus.COMPLETED: set(),
            RentalStatus.CANCELED: set(),
        }
        if new_status not in allowed_transitions[self.status]:
            raise InvalidStateTransitionException()
        self.status = new_status
