from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.models import Rental, Reservation
from rentals.services.rental_query import RentalQuery


class RentalQueryTests(APITestCase):
    def setUp(self):
        user = User.objects.create_user(username='attendant', password='test')
        self.client.force_authenticate(user=user)
        self.starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        self.first = self.create_rental(
            customer_id=41,
            vehicle_id=12,
            pickup_branch_id=3,
            return_branch_id=5,
            status=RentalStatus.COMPLETED,
            actual_return_branch_id=5,
            starts_at=self.starts_at,
        )
        self.second = self.create_rental(
            customer_id=42,
            vehicle_id=13,
            pickup_branch_id=4,
            return_branch_id=4,
            status=RentalStatus.OVERDUE,
            actual_return_branch_id=None,
            starts_at=self.starts_at + timedelta(days=2),
        )
        self.query_patch = patch(
            'rentals.api.views.get_rental_query',
            return_value=RentalQuery(),
        )
        self.query_patch.start()
        self.addCleanup(self.query_patch.stop)

    def create_rental(
        self,
        *,
        customer_id,
        vehicle_id,
        pickup_branch_id,
        return_branch_id,
        status,
        actual_return_branch_id,
        starts_at,
    ):
        reservation = Reservation.objects.create(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            pickup_branch_id=pickup_branch_id,
            return_branch_id=return_branch_id,
            insurance_id=None,
            starts_at=starts_at,
            expected_return_at=starts_at + timedelta(days=1),
            status=(
                ReservationStatus.FULFILLED
                if status != RentalStatus.RESERVED
                else ReservationStatus.CONFIRMED
            ),
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('120.00'),
            first_day_amount_snapshot=Decimal('120.00'),
        )
        return Rental.objects.create(
            reservation=reservation,
            status=status,
            actual_return_branch_id=actual_return_branch_id,
        )

    def test_customer_status_pickup_branch_and_period_filters(self):
        query = RentalQuery()

        self.assertEqual(list(query.list_by_customer(41)), [self.first])
        self.assertEqual(list(query.list_overdue()), [self.second])
        self.assertEqual(
            list(
                query.list_by_period(
                    branch_id=3,
                    start=self.starts_at,
                    end=self.starts_at + timedelta(days=2),
                )
            ),
            [self.first],
        )

    def test_rental_api_filters_and_preserves_distinct_return_branch(self):
        response = self.client.get(
            '/api/rentals',
            {
                'customer_id': 41,
                'status': RentalStatus.COMPLETED,
                'pickup_branch_id': 3,
                'starts_at': self.starts_at.isoformat(),
                'expected_return_at': (self.starts_at + timedelta(days=2)).isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        result = response.data['results'][0]
        self.assertEqual(result['pickup_branch_id'], 3)
        self.assertEqual(result['return_branch_id'], 5)
        self.assertEqual(result['actual_return_branch_id'], 5)
        self.assertEqual(response.data['overdue_alerts'], [])
