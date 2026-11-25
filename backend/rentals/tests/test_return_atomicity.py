from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TransactionTestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.models import Rental, Reservation
from rentals.services.ports import Inspection
from rentals.services.rental_service import RentalService
from rentals.tests.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeInsuranceService,
    FakeVehicleService,
)


class RentalReturnAtomicityTests(TransactionTestCase):
    def setUp(self):
        starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        reservation = Reservation.objects.create(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=3,
            insurance_id=None,
            starts_at=starts_at,
            expected_return_at=starts_at + timedelta(days=3),
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
        self.vehicle_service = FakeVehicleService()
        self.vehicle_service.rented_vehicle_ids.add(12)
        self.inspection_service = FakeInspectionService()
        self.inspection_service.inspections[(self.rental.pk, 'ENTRY')] = Inspection(
            inspection_id=902,
            inspection_type='ENTRY',
        )
        self.finance_service = FakeFinanceService()
        self.service = RentalService(
            vehicle_service=self.vehicle_service,
            inspection_service=self.inspection_service,
            customer_service=FakeCustomerService(),
            payment_service=self.finance_service,
            fine_service=self.finance_service,
            finance_query=self.finance_service,
            insurance_service=FakeInsuranceService(),
        )

    def return_rental(self):
        return self.service.return_vehicle(
            self.rental.pk,
            inspection_id=902,
            return_branch_id=3,
            now=datetime(2030, 1, 4, 10, tzinfo=UTC),
        )

    def assert_return_rolled_back(self):
        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.PICKED_UP)
        self.assertIsNone(self.rental.returned_at)
        self.assertIn(12, self.vehicle_service.rented_vehicle_ids)
        self.assertEqual(self.finance_service.charges, [])

    def test_charge_provider_failure_rolls_back_return(self):
        self.finance_service.fail_on.add('create_pending_charge')

        with self.assertRaises(RuntimeError):
            self.return_rental()

        self.assert_return_rolled_back()

    def test_fleet_release_failure_rolls_back_charges_and_return(self):
        self.vehicle_service.fail_on.add('release')

        with self.assertRaises(RuntimeError):
            self.return_rental()

        self.assert_return_rolled_back()

    def test_retry_after_failure_does_not_duplicate_charges(self):
        self.vehicle_service.fail_on.add('release')
        with self.assertRaises(RuntimeError):
            self.return_rental()

        self.vehicle_service.fail_on.clear()
        self.return_rental()

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.RETURNED)
        self.assertEqual(len(self.finance_service.charges), 1)
        self.assertEqual(self.finance_service.charges[0][2], 'RENTAL_BASE')
