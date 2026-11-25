from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TransactionTestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import PendingInspectionException
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


class RentalReturnServiceTests(TransactionTestCase):
    def setUp(self):
        self.starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.due_at = self.starts_at + timedelta(days=3)
        self.reservation = Reservation.objects.create(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=5,
            insurance_id=2,
            starts_at=self.starts_at,
            expected_return_at=self.due_at,
            status=ReservationStatus.FULFILLED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('435.00'),
            first_day_amount_snapshot=Decimal('145.00'),
        )
        self.rental = Rental.objects.create(
            reservation=self.reservation,
            status=RentalStatus.PICKED_UP,
            deposit_required_snapshot=Decimal('300.00'),
        )
        self.vehicle_service = FakeVehicleService()
        self.vehicle_service.rented_vehicle_ids.add(12)
        self.inspection_service = FakeInspectionService()
        self.finance_service = FakeFinanceService()
        self.insurance_service = FakeInsuranceService()
        self.service = RentalService(
            vehicle_service=self.vehicle_service,
            inspection_service=self.inspection_service,
            customer_service=FakeCustomerService(),
            payment_service=self.finance_service,
            fine_service=self.finance_service,
            finance_query=self.finance_service,
            insurance_service=self.insurance_service,
            inter_branch_fee=Decimal('79.99'),
        )

    def register_entry_inspection(self, *, has_damage=False):
        self.inspection_service.inspections[(self.rental.pk, 'ENTRY')] = Inspection(
            inspection_id=902,
            inspection_type='ENTRY',
            has_damage=has_damage,
        )

    def return_at(self, returned_at, *, return_branch_id=3):
        return self.service.return_vehicle(
            self.rental.pk,
            inspection_id=902,
            return_branch_id=return_branch_id,
            now=returned_at,
        )

    def test_return_requires_a_persisted_entry_inspection(self):
        with self.assertRaises(PendingInspectionException):
            self.return_at(self.due_at)

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.PICKED_UP)

    def test_exact_one_hour_grace_has_no_late_charge(self):
        self.register_entry_inspection()

        result = self.return_at(self.due_at + timedelta(hours=1))

        self.assertEqual(result.late_day_count, 0)
        self.assertEqual(result.late_charge_amount, Decimal('0.00'))

    def test_late_starts_after_the_exact_grace_boundary(self):
        self.register_entry_inspection()

        result = self.return_at(
            self.due_at + timedelta(hours=1, seconds=1),
        )
        self.assertEqual(result.late_day_count, 1)

    def test_each_started_24_hour_period_counts_as_a_day(self):
        self.register_entry_inspection()
        later = self.return_at(self.due_at + timedelta(hours=25, seconds=1))

        self.assertEqual(later.late_day_count, 2)
        self.assertEqual(later.late_charge_amount, Decimal('264.00'))

    def test_inter_branch_fee_is_fixed_and_damage_is_included(self):
        self.register_entry_inspection(has_damage=True)
        self.insurance_service.damage_costs[902] = Decimal('65.50')

        result = self.return_at(self.due_at, return_branch_id=5)

        self.assertEqual(result.inter_branch_charge_amount, Decimal('79.99'))
        self.assertEqual(result.damage_charge_amount, Decimal('65.50'))
        self.assertEqual(
            result.balance_due,
            Decimal('580.49'),
        )
        self.rental.refresh_from_db()
        self.assertEqual(self.rental.actual_return_branch_id, 5)

    def test_same_pickup_and_return_branch_has_no_inter_branch_fee(self):
        self.register_entry_inspection()

        result = self.return_at(self.due_at, return_branch_id=3)

        self.assertEqual(result.inter_branch_charge_amount, Decimal('0.00'))
