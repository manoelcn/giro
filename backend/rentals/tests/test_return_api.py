from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

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


class RentalReturnApiTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='attendant', password='test')
        self.client.force_authenticate(user=user)
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
            inter_branch_fee=Decimal('79.99'),
        )
        self.service_patch = patch(
            'rentals.api.views.get_rental_service',
            return_value=self.service,
        )
        self.service_patch.start()
        self.addCleanup(self.service_patch.stop)

    def test_return_endpoint_reports_charge_breakdown(self):
        response = self.client.post(
            f'/api/rentals/{self.rental.pk}/return',
            {'inspection_id': 902, 'return_branch_id': 5},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], RentalStatus.RETURNED)
        self.assertEqual(response.data['inter_branch_charge_amount'], '79.99')
        self.assertEqual(response.data['balance_due'], '514.99')

    def test_finalize_endpoint_reports_pending_balance_as_conflict(self):
        self.finance_service.balances_due[self.rental.pk] = Decimal('50.00')
        self.finance_service.deposits[self.rental.pk] = Decimal('20.00')
        self.rental.status = RentalStatus.RETURNED
        self.rental.save(update_fields=['status'])

        response = self.client.post(f'/api/rentals/{self.rental.pk}/finalize')

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'PENDING_BALANCE')
        self.assertEqual(response.data['fields']['balance_due'], '30.00')
