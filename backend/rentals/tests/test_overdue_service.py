from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.models import Rental, Reservation
from rentals.services.rental_service import RentalService
from rentals.tests.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeInsuranceService,
    FakeVehicleService,
)


class RentalOverdueServiceTests(TestCase):
    def setUp(self):
        self.expected_return_at = datetime(2030, 1, 4, 10, tzinfo=UTC)
        reservation = Reservation.objects.create(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=3,
            insurance_id=None,
            starts_at=datetime(2030, 1, 1, 10, tzinfo=UTC),
            expected_return_at=self.expected_return_at,
            status=ReservationStatus.FULFILLED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('435.00'),
            first_day_amount_snapshot=Decimal('145.00'),
        )
        self.rental = Rental.objects.create(
            reservation=reservation,
            status=RentalStatus.PICKED_UP,
            deposit_required_snapshot=Decimal('300.00'),
        )
        self.future_reservation = Reservation.objects.create(
            customer_id=55,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=3,
            insurance_id=None,
            starts_at=self.expected_return_at + timedelta(hours=2),
            expected_return_at=self.expected_return_at + timedelta(days=1),
            status=ReservationStatus.CONFIRMED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('120.00'),
            first_day_amount_snapshot=Decimal('120.00'),
        )
        Rental.objects.create(
            reservation=self.future_reservation,
            status=RentalStatus.RESERVED,
            deposit_required_snapshot=Decimal('300.00'),
        )
        self.vehicle_service = FakeVehicleService()
        self.vehicle_service.equivalent_vehicle_ids[12] = [77]
        self.service = RentalService(
            vehicle_service=self.vehicle_service,
            inspection_service=FakeInspectionService(),
            customer_service=FakeCustomerService(),
            payment_service=FakeFinanceService(),
            fine_service=FakeFinanceService(),
            finance_query=FakeFinanceService(),
            insurance_service=FakeInsuranceService(),
        )

    def test_exact_one_hour_boundary_is_not_overdue(self):
        alerts = self.service.verify_overdue(
            self.expected_return_at + timedelta(hours=1),
        )

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.PICKED_UP)
        self.assertEqual(alerts, [])

    def test_overdue_transition_is_idempotent_and_suggests_only_available_equivalents(self):
        now = self.expected_return_at + timedelta(hours=1, seconds=1)

        first_alerts = self.service.verify_overdue(now)
        second_alerts = self.service.verify_overdue(now)

        self.rental.refresh_from_db()
        self.future_reservation.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.OVERDUE)
        self.assertEqual(len(first_alerts), 1)
        self.assertEqual(first_alerts, second_alerts)
        self.assertEqual(first_alerts[0].equivalent_vehicle_ids, [77])
        self.assertEqual(self.future_reservation.vehicle_id, 12)

    def test_alert_is_kept_when_no_equivalent_vehicle_is_available(self):
        self.vehicle_service.equivalent_vehicle_ids[12] = []

        alerts = self.service.verify_overdue(
            self.expected_return_at + timedelta(hours=1, seconds=2),
        )

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].equivalent_vehicle_ids, [])
