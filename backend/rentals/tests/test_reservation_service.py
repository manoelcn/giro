from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import ConflictingReservationException
from rentals.models import Rental, Reservation
from rentals.services.ports import Quote, RentalTerms
from rentals.services.reservation_query import ReservationQuery
from rentals.services.reservation_service import ReservationService
from rentals.tests.fakes import FakeQuoteService, FakeVehicleService


class ReservationServiceTests(TestCase):
    def setUp(self):
        self.vehicle_id = 12
        self.starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.expected_return_at = self.starts_at + timedelta(days=3)
        self.vehicle_service = FakeVehicleService()
        self.vehicle_service.terms[self.vehicle_id] = RentalTerms(
            daily_rate=Decimal('120.00'),
            minimum_deposit=Decimal('300.00'),
            operational=True,
        )
        self.quote_service = FakeQuoteService()
        self.quote_service.result = Quote(
            daily_rate=Decimal('120.00'),
            first_day_amount=Decimal('145.00'),
            quoted_total=Decimal('435.00'),
        )
        self.service = ReservationService(
            vehicle_service=self.vehicle_service,
            quote_service=self.quote_service,
        )

    def create_reservation(self, **overrides):
        values = {
            'customer_id': 41,
            'vehicle_id': self.vehicle_id,
            'starts_at': self.starts_at,
            'expected_return_at': self.expected_return_at,
            'pickup_branch_id': 3,
            'return_branch_id': 5,
            'insurance_id': 2,
            'accepted_total': Decimal('435.00'),
        }
        values.update(overrides)
        return self.service.create(**values)

    def test_rejects_overlapping_confirmed_reservation(self):
        self.create_reservation()

        with self.assertRaises(ConflictingReservationException):
            self.create_reservation(starts_at=self.starts_at + timedelta(days=1))

        self.assertEqual(Reservation.objects.count(), 1)

    def test_canceled_reservation_does_not_occupy_vehicle(self):
        Reservation.objects.create(
            customer_id=99,
            vehicle_id=self.vehicle_id,
            pickup_branch_id=3,
            return_branch_id=5,
            insurance_id=None,
            starts_at=self.starts_at,
            expected_return_at=self.expected_return_at,
            status=ReservationStatus.CANCELED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('435.00'),
            first_day_amount_snapshot=Decimal('145.00'),
        )

        reservation, _ = self.create_reservation()

        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_active_rental_occupies_its_reserved_period(self):
        reservation = Reservation.objects.create(
            customer_id=99,
            vehicle_id=self.vehicle_id,
            pickup_branch_id=3,
            return_branch_id=5,
            insurance_id=None,
            starts_at=self.starts_at,
            expected_return_at=self.expected_return_at,
            status=ReservationStatus.FULFILLED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('435.00'),
            first_day_amount_snapshot=Decimal('145.00'),
        )
        Rental.objects.create(
            reservation=reservation,
            status=RentalStatus.PICKED_UP,
            deposit_required_snapshot=Decimal('300.00'),
        )

        with self.assertRaises(ConflictingReservationException):
            self.create_reservation()

    def test_allows_consecutive_half_open_periods(self):
        self.create_reservation()

        next_reservation, _ = self.create_reservation(
            starts_at=self.expected_return_at,
            expected_return_at=self.expected_return_at + timedelta(days=2),
        )

        self.assertEqual(next_reservation.starts_at, self.expected_return_at)
        self.assertEqual(Reservation.objects.count(), 2)

    def test_busy_vehicle_query_includes_open_rentals_after_scheduled_return(self):
        _, rental = self.create_reservation()
        rental.status = RentalStatus.PICKED_UP
        rental.save(update_fields=['status'])
        later_start = self.expected_return_at + timedelta(days=1)
        query = ReservationQuery()

        self.assertEqual(
            query.busy_vehicle_ids(later_start, later_start + timedelta(days=1)),
            {self.vehicle_id},
        )

        rental.status = RentalStatus.COMPLETED
        rental.save(update_fields=['status'])
        self.assertEqual(
            query.busy_vehicle_ids(later_start, later_start + timedelta(days=1)),
            set(),
        )
