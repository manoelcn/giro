from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import (
    CustomerIneligibleException,
    InsufficientDepositException,
    InvalidStateTransitionException,
    PendingInspectionException,
)
from rentals.models import Rental, Reservation
from rentals.services.ports import Inspection
from rentals.services.rental_service import RentalService
from rentals.tests.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeVehicleService,
)


class PickupTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='attendant', password='test')
        self.client.force_authenticate(user=self.user)
        starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.reservation = Reservation.objects.create(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=5,
            insurance_id=None,
            starts_at=starts_at,
            expected_return_at=starts_at + timedelta(days=3),
            status=ReservationStatus.CONFIRMED,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('435.00'),
            first_day_amount_snapshot=Decimal('145.00'),
        )
        self.rental = Rental.objects.create(
            reservation=self.reservation,
            status=RentalStatus.RESERVED,
            deposit_required_snapshot=Decimal('300.00'),
        )
        self.vehicle_service = FakeVehicleService()
        self.inspection_service = FakeInspectionService()
        self.customer_service = FakeCustomerService()
        self.finance_service = FakeFinanceService()
        self.service = RentalService(
            vehicle_service=self.vehicle_service,
            inspection_service=self.inspection_service,
            customer_service=self.customer_service,
            payment_service=self.finance_service,
        )
        self.service_patch = patch(
            'rentals.api.views.get_rental_service',
            return_value=self.service,
        )
        self.service_patch.start()
        self.addCleanup(self.service_patch.stop)

    def register_exit_inspection(self, inspection_id=901):
        self.inspection_service.inspections[(self.rental.pk, 'EXIT')] = Inspection(
            inspection_id=inspection_id,
            inspection_type='EXIT',
        )

    def test_missing_inspection_preserves_reservation_and_rental(self):
        with self.assertRaises(PendingInspectionException):
            self.service.pick_up(self.rental.pk, inspection_id=901)

        self.rental.refresh_from_db()
        self.reservation.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.RESERVED)
        self.assertEqual(self.reservation.status, ReservationStatus.CONFIRMED)

    def test_insufficient_deposit_preserves_states(self):
        self.register_exit_inspection()

        with self.assertRaises(InsufficientDepositException):
            self.service.pick_up(self.rental.pk, inspection_id=901)

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.RESERVED)

    def test_ineligible_customer_cannot_pick_up(self):
        self.register_exit_inspection()
        self.customer_service.ineligible_customer_ids.add(41)
        self.finance_service.deposits[self.rental.pk] = Decimal('300.00')

        with self.assertRaises(CustomerIneligibleException):
            self.service.pick_up(self.rental.pk, inspection_id=901)

        self.rental.refresh_from_db()
        self.assertEqual(self.rental.status, RentalStatus.RESERVED)

    def test_invalid_state_transition_is_rejected(self):
        self.rental.status = RentalStatus.RETURNED
        self.rental.save(update_fields=['status'])
        self.register_exit_inspection()
        self.finance_service.deposits[self.rental.pk] = Decimal('300.00')

        with self.assertRaises(InvalidStateTransitionException):
            self.service.pick_up(self.rental.pk, inspection_id=901)

    def test_successful_pickup_fulfills_reservation_and_marks_vehicle_rented(self):
        self.register_exit_inspection()
        self.finance_service.deposits[self.rental.pk] = Decimal('300.00')
        picked_up_at = datetime(2030, 1, 1, 10, tzinfo=UTC)

        with self.captureOnCommitCallbacks(execute=True):
            result = self.service.pick_up(
                self.rental.pk,
                inspection_id=901,
                now=picked_up_at,
            )

        self.rental.refresh_from_db()
        self.reservation.refresh_from_db()
        self.assertEqual(result.status, RentalStatus.PICKED_UP)
        self.assertEqual(self.rental.picked_up_at, picked_up_at)
        self.assertEqual(self.reservation.status, ReservationStatus.FULFILLED)
        self.assertIn(12, self.vehicle_service.rented_vehicle_ids)

    def test_pickup_api_returns_pending_inspection_code(self):
        response = self.client.post(
            f'/api/rentals/{self.rental.pk}/pick-up',
            {'inspection_id': 901},
            format='json',
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data['code'], 'PENDING_INSPECTION')
