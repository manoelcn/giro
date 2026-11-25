from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier

from django.db import close_old_connections
from django.test import TransactionTestCase

from rentals.domain.exceptions import ConflictingReservationException
from rentals.domain.exceptions import DatabaseContentionException
from rentals.services.ports import Quote, RentalTerms
from rentals.services.reservation_service import ReservationService
from rentals.tests.fakes import FakeQuoteService, FakeVehicleService


class ReservationConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_one_hundred_simultaneous_pairs_never_confirm_both_reservations(self):
        vehicle_service = FakeVehicleService()
        quote_service = FakeQuoteService()
        quote_service.result = Quote(
            daily_rate=Decimal('120.00'),
            first_day_amount=Decimal('145.00'),
            quoted_total=Decimal('435.00'),
        )
        service = ReservationService(
            vehicle_service=vehicle_service,
            quote_service=quote_service,
        )
        starts_at = datetime(2030, 1, 1, 10, tzinfo=UTC)
        expected_return_at = starts_at + timedelta(days=3)
        confirmed_per_pair = []

        def attempt_pair(vehicle_id: int) -> int:
            barrier = Barrier(2)

            def create_reservation() -> bool:
                close_old_connections()
                try:
                    barrier.wait()
                    service.create(
                        customer_id=vehicle_id,
                        vehicle_id=vehicle_id,
                        starts_at=starts_at,
                        expected_return_at=expected_return_at,
                        pickup_branch_id=3,
                        return_branch_id=5,
                        insurance_id=None,
                        accepted_total=Decimal('435.00'),
                    )
                    return True
                except ConflictingReservationException:
                    return False
                except DatabaseContentionException:
                    return False
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: create_reservation(), range(2)))
            return sum(results)

        for vehicle_id in range(1000, 1100):
            vehicle_service.terms[vehicle_id] = RentalTerms(
                daily_rate=Decimal('120.00'),
                minimum_deposit=Decimal('300.00'),
                operational=True,
            )
            confirmed_per_pair.append(attempt_pair(vehicle_id))

        self.assertEqual(confirmed_per_pair, [1] * 100)
