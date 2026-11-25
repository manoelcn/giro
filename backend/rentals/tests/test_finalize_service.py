from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TransactionTestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import PendingBalanceException
from rentals.models import Rental, Reservation
from rentals.services.rental_service import RentalService
from rentals.tests.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeInsuranceService,
    FakeVehicleService,
)


class RentalFinalizeServiceTests(TransactionTestCase):
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
            status=RentalStatus.RETURNED,
            deposit_required_snapshot=Decimal('300.00'),
            returned_at=datetime(2030, 1, 4, 10, tzinfo=UTC),
        )
        self.finance_service = FakeFinanceService()
        self.service = RentalService(
            vehicle_service=FakeVehicleService(),
            inspection_service=FakeInspectionService(),
            customer_service=FakeCustomerService(),
            payment_service=self.finance_service,
            fine_service=self.finance_service,
            finance_query=self.finance_service,
            insurance_service=FakeInsuranceService(),
        )

    def test_partial_deposit_application_keeps_rental_returned_and_reports_balance(self):
        self.finance_service.balances_due[self.rental.pk] = Decimal('50.00')
        self.finance_service.deposits[self.rental.pk] = Decimal('20.00')

        with self.assertRaises(PendingBalanceException) as raised:
            self.service.finalize(self.rental.pk)

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.RETURNED)
        self.assertEqual(self.finance_service.balance_due(self.rental.pk), Decimal('30.00'))
        self.assertEqual(self.finance_service.deposits[self.rental.pk], Decimal('0.00'))
        self.assertEqual(raised.exception.fields['balance_due'], '30.00')

    def test_settled_balance_completes_and_releases_deposit_remainder(self):
        self.finance_service.balances_due[self.rental.pk] = Decimal('50.00')
        self.finance_service.deposits[self.rental.pk] = Decimal('100.00')

        result = self.service.finalize(self.rental.pk)

        self.rental.refresh_from_db()
        self.assertEqual(result.status, RentalStatus.COMPLETED)
        self.assertEqual(self.finance_service.balance_due(self.rental.pk), Decimal('0.00'))
        self.assertEqual(
            self.finance_service.released_deposits[self.rental.pk],
            Decimal('50.00'),
        )

    def test_retry_after_settlement_finishes_without_releasing_unpaid_remainder(self):
        self.finance_service.balances_due[self.rental.pk] = Decimal('50.00')
        self.finance_service.deposits[self.rental.pk] = Decimal('20.00')
        with self.assertRaises(PendingBalanceException):
            self.service.finalize(self.rental.pk)

        self.finance_service.balances_due[self.rental.pk] = Decimal('0.00')
        result = self.service.finalize(self.rental.pk)

        self.assertEqual(result.status, RentalStatus.COMPLETED)
        self.assertEqual(
            self.finance_service.released_deposits[self.rental.pk],
            Decimal('0.00'),
        )
