from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from rentals.services.ports import Quote, RentalTerms
from rentals.services.reservation_service import ReservationService
from rentals.tests.fakes import FakeQuoteService, FakeVehicleService


class ReservationsApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='attendant', password='test')
        self.client.force_authenticate(user=self.user)
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
        self.reservation_service = ReservationService(
            vehicle_service=self.vehicle_service,
            quote_service=self.quote_service,
        )
        self.service_patch = patch(
            'rentals.api.views.get_reservation_service',
            return_value=self.reservation_service,
        )
        self.service_patch.start()
        self.addCleanup(self.service_patch.stop)

    def reservation_payload(self):
        return {
            'customer_id': 41,
            'vehicle_id': 12,
            'starts_at': self.starts_at.isoformat(),
            'expected_return_at': self.expected_return_at.isoformat(),
            'pickup_branch_id': 3,
            'return_branch_id': 5,
            'insurance_id': 2,
        }

    def test_quote_returns_decimal_strings(self):
        response = self.client.post(
            '/api/reservations/quote',
            self.reservation_payload(),
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['daily_rate'], '120.00')
        self.assertEqual(response.data['quoted_total'], '435.00')

    def test_confirmation_rejects_changed_quote_without_creating_records(self):
        self.quote_service.result = Quote(
            daily_rate=Decimal('125.00'),
            first_day_amount=Decimal('150.00'),
            quoted_total=Decimal('450.00'),
        )
        response = self.client.post(
            '/api/reservations',
            {**self.reservation_payload(), 'accepted_total': '435.00'},
            format='json',
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data['code'], 'QUOTE_CHANGED')

    def test_retrieval_and_list_filters_return_created_reservation(self):
        create_response = self.client.post(
            '/api/reservations',
            {**self.reservation_payload(), 'accepted_total': '435.00'},
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)
        reservation_id = create_response.data['id']

        detail_response = self.client.get(f'/api/reservations/{reservation_id}')
        list_response = self.client.get('/api/reservations', {'customer_id': 41})
        filtered_response = self.client.get('/api/reservations', {'customer_id': 99})

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.data['id'], reservation_id)
        self.assertEqual(list_response.data['count'], 1)
        self.assertEqual(list_response.data['results'][0]['id'], reservation_id)
        self.assertEqual(filtered_response.data['count'], 0)
