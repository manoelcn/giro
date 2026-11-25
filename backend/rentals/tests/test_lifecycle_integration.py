from datetime import UTC, datetime, timedelta
from decimal import Decimal

from django.test import TransactionTestCase

from rentals.domain.enums import RentalStatus
from rentals.services.ports import Inspection, Quote, RentalTerms
from rentals.services.rental_service import RentalService
from rentals.services.reservation_service import ReservationService
from rentals.tests.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeInsuranceService,
    FakeQuoteService,
    FakeVehicleService,
)


class RentalLifecycleIntegrationTests(TransactionTestCase):
    def setUp(self):
        self.starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.expected_return_at = self.starts_at + timedelta(days=3)
        self.vehicle_service = FakeVehicleService()
        self.vehicle_service.terms[12] = RentalTerms(
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
        self.finance_service = FakeFinanceService()
        self.inspection_service = FakeInspectionService()
        self.reservation_service = ReservationService(
            vehicle_service=self.vehicle_service,
            quote_service=self.quote_service,
            payment_service=self.finance_service,
        )
        self.rental_service = RentalService(
            vehicle_service=self.vehicle_service,
            inspection_service=self.inspection_service,
            customer_service=FakeCustomerService(),
            payment_service=self.finance_service,
            fine_service=self.finance_service,
            finance_query=self.finance_service,
            insurance_service=FakeInsuranceService(),
        )

    def reservation_input(self):
        return {
            'customer_id': 41,
            'vehicle_id': 12,
            'starts_at': self.starts_at,
            'expected_return_at': self.expected_return_at,
            'pickup_branch_id': 3,
            'return_branch_id': 3,
            'insurance_id': None,
        }

    def create_rental(self):
        inputs = self.reservation_input()
        quote = self.reservation_service.quote(**inputs)
        _, rental = self.reservation_service.create(
            **inputs,
            accepted_total=quote.quoted_total,
        )
        self.finance_service.deposits[rental.pk] = Decimal('500.00')
        self.inspection_service.inspections[(rental.pk, 'EXIT')] = Inspection(
            inspection_id=901,
            inspection_type='EXIT',
        )
        return rental

    def test_quote_reservation_pickup_return_and_settlement(self):
        rental = self.create_rental()

        self.assertEqual(rental.status, RentalStatus.RESERVED)
        self.rental_service.pick_up(
            rental.pk,
            inspection_id=901,
            now=self.starts_at,
        )
        self.inspection_service.inspections[(rental.pk, 'ENTRY')] = Inspection(
            inspection_id=902,
            inspection_type='ENTRY',
        )
        result = self.rental_service.return_vehicle(
            rental.pk,
            inspection_id=902,
            return_branch_id=3,
            now=self.expected_return_at,
        )
        finalized = self.rental_service.finalize(rental.pk)

        rental.refresh_from_db()
        self.assertEqual(result.balance_due, Decimal('435.00'))
        self.assertEqual(finalized.status, RentalStatus.COMPLETED)
        self.assertEqual(rental.status, RentalStatus.COMPLETED)
        self.assertEqual(self.finance_service.balance_due(rental.pk), Decimal('0.00'))
        self.assertEqual(
            self.finance_service.released_deposits[rental.pk],
            Decimal('65.00'),
        )
        self.assertNotIn(12, self.vehicle_service.rented_vehicle_ids)

    def test_failed_vehicle_release_rolls_back_return_and_pending_charges(self):
        rental = self.create_rental()
        self.rental_service.pick_up(
            rental.pk,
            inspection_id=901,
            now=self.starts_at,
        )
        self.inspection_service.inspections[(rental.pk, 'ENTRY')] = Inspection(
            inspection_id=902,
            inspection_type='ENTRY',
        )
        self.vehicle_service.fail_on.add('release')

        with self.assertRaises(RuntimeError):
            self.rental_service.return_vehicle(
                rental.pk,
                inspection_id=902,
                return_branch_id=3,
                now=self.expected_return_at,
            )

        rental.refresh_from_db()
        self.assertEqual(rental.status, RentalStatus.PICKED_UP)
        self.assertIsNone(rental.returned_at)
        self.assertEqual(self.finance_service.charges, [])
        self.assertIn(12, self.vehicle_service.rented_vehicle_ids)
