from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import (
    CancellationDeadlineExceededException,
)
from rentals.models import Rental, Reservation
from rentals.services.ports import Quote, RentalTerms
from rentals.services.reservation_service import ReservationService
from rentals.tests.fakes import FakeFinanceService, FakeQuoteService, FakeVehicleService


class ReservationCancellationTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='attendant', password='test')
        self.client.force_authenticate(user=user)
        self.now = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.starts_at = self.now + timedelta(hours=48)
        self.reservation = Reservation.objects.create(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=3,
            insurance_id=None,
            starts_at=self.starts_at,
            expected_return_at=self.starts_at + timedelta(days=3),
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
        self.service = ReservationService(
            vehicle_service=self.vehicle_service,
            quote_service=self.quote_service,
            payment_service=self.finance_service,
        )
        self.service_patch = patch(
            'rentals.api.views.get_reservation_service',
            return_value=self.service,
        )
        self.service_patch.start()
        self.addCleanup(self.service_patch.stop)

    def test_exact_24_hour_cancellation_is_free(self):
        self.reservation.starts_at = self.now + timedelta(hours=24)
        self.reservation.save(update_fields=['starts_at'])

        with self.captureOnCommitCallbacks(execute=True):
            result = self.service.cancel(self.reservation.pk, now=self.now)

        self.reservation.refresh_from_db()
        self.rental.refresh_from_db()
        self.assertIsNone(result.cancellation_charge)
        self.assertEqual(self.reservation.status, ReservationStatus.CANCELED)
        self.assertEqual(self.rental.status, RentalStatus.CANCELED)
        self.assertEqual(self.finance_service.charges, [])

    def test_cancellation_inside_24_hours_creates_pending_twenty_percent_charge(self):
        self.reservation.starts_at = self.now + timedelta(hours=23)
        self.reservation.save(update_fields=['starts_at'])

        with self.captureOnCommitCallbacks(execute=True):
            result = self.service.cancel(self.reservation.pk, now=self.now)

        self.rental.refresh_from_db()
        self.assertEqual(result.cancellation_charge.amount, Decimal('29.00'))
        self.assertEqual(result.cancellation_charge.status, 'PENDING')
        self.assertEqual(self.rental.cancellation_charge_id, result.cancellation_charge.id)
        self.assertEqual(self.finance_service.charges[0][2], 'CANCELLATION')

    def test_pending_charge_provider_failure_rolls_back_cancellation(self):
        self.reservation.starts_at = self.now + timedelta(hours=23)
        self.reservation.save(update_fields=['starts_at'])
        self.finance_service.fail_on.add('create_pending_charge')

        with self.assertRaises(RuntimeError):
            self.service.cancel(self.reservation.pk, now=self.now)

        self.reservation.refresh_from_db()
        self.rental.refresh_from_db()
        self.assertEqual(self.reservation.status, ReservationStatus.CONFIRMED)
        self.assertEqual(self.rental.status, RentalStatus.RESERVED)
        self.assertEqual(self.finance_service.charges, [])

    def test_cannot_cancel_after_pickup(self):
        self.reservation.status = ReservationStatus.FULFILLED
        self.reservation.save(update_fields=['status'])
        self.rental.status = RentalStatus.PICKED_UP
        self.rental.save(update_fields=['status'])

        with self.assertRaises(CancellationDeadlineExceededException):
            self.service.cancel(self.reservation.pk, now=self.now)

    def test_cancelled_period_can_be_reserved_again(self):
        self.reservation.starts_at = self.now + timedelta(hours=23)
        self.reservation.save(update_fields=['starts_at'])
        with self.captureOnCommitCallbacks(execute=True):
            self.service.cancel(self.reservation.pk, now=self.now)

        next_reservation, _ = self.service.create(
            customer_id=42,
            vehicle_id=12,
            starts_at=self.reservation.starts_at,
            expected_return_at=self.reservation.expected_return_at,
            pickup_branch_id=3,
            return_branch_id=3,
            insurance_id=None,
            accepted_total=Decimal('435.00'),
        )

        self.assertEqual(next_reservation.status, ReservationStatus.CONFIRMED)

    def test_cancel_preview_reports_pending_charge_before_confirmation(self):
        self.reservation.starts_at = self.now + timedelta(hours=23)
        self.reservation.save(update_fields=['starts_at'])

        with patch(
            'rentals.services.reservation_service.timezone.now',
            return_value=self.now,
        ):
            response = self.client.get(
                f'/api/reservations/{self.reservation.pk}/cancel',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['cancellation_charge']['amount'], '29.00')
