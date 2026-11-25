from datetime import UTC, datetime, timedelta

from django.test import SimpleTestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import InvalidStateTransitionException
from rentals.domain.rental import Rental
from rentals.domain.reservation import Reservation


class RentalDomainStateTests(SimpleTestCase):
    def test_reservation_and_rental_follow_valid_lifecycle_transitions(self):
        starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        reservation = Reservation(
            customer_id=41,
            vehicle_id=12,
            starts_at=starts_at,
            expected_return_at=starts_at + timedelta(days=3),
        )
        rental = Rental(reservation_id=77)

        reservation.transition_to(ReservationStatus.FULFILLED)
        rental.transition_to(RentalStatus.PICKED_UP)
        rental.transition_to(RentalStatus.OVERDUE)
        rental.transition_to(RentalStatus.RETURNED)
        rental.transition_to(RentalStatus.COMPLETED)

        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)
        self.assertEqual(rental.status, RentalStatus.COMPLETED)

    def test_rejects_transitions_outside_the_state_machine(self):
        reservation = Reservation(
            customer_id=41,
            vehicle_id=12,
            starts_at=datetime(2030, 1, 1, 10, tzinfo=UTC),
            expected_return_at=datetime(2030, 1, 4, 10, tzinfo=UTC),
            status=ReservationStatus.CANCELED,
        )
        rental = Rental(reservation_id=77, status=RentalStatus.COMPLETED)

        with self.assertRaises(InvalidStateTransitionException):
            reservation.transition_to(ReservationStatus.FULFILLED)
        with self.assertRaises(InvalidStateTransitionException):
            rental.transition_to(RentalStatus.RETURNED)
