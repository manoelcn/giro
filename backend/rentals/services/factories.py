from decimal import Decimal

from django.conf import settings

from rentals.services.fakes import (
    FakeCustomerService,
    FakeFinanceService,
    FakeInspectionService,
    FakeInsuranceService,
    FakeQuoteService,
    FakeVehicleService,
)
from rentals.services.ports import Quote, RentalTerms
from rentals.services.rental_service import RentalService
from rentals.services.reservation_service import ReservationService


_vehicle_service = FakeVehicleService()
_vehicle_service.terms[12] = RentalTerms(
    daily_rate=Decimal('120.00'),
    minimum_deposit=Decimal('300.00'),
    operational=True,
)
_quote_service = FakeQuoteService()
_quote_service.result = Quote(
    daily_rate=Decimal('120.00'),
    first_day_amount=Decimal('145.00'),
    quoted_total=Decimal('435.00'),
)
_customer_service = FakeCustomerService()
_finance_service = FakeFinanceService()
_inspection_service = FakeInspectionService()
_insurance_service = FakeInsuranceService()


def get_reservation_service() -> ReservationService:
    return ReservationService(
        vehicle_service=_vehicle_service,
        quote_service=_quote_service,
        payment_service=_finance_service,
    )


def get_rental_service() -> RentalService:
    return RentalService(
        vehicle_service=_vehicle_service,
        inspection_service=_inspection_service,
        customer_service=_customer_service,
        payment_service=_finance_service,
        fine_service=_finance_service,
        finance_query=_finance_service,
        insurance_service=_insurance_service,
        inter_branch_fee=settings.RENTALS_INTER_BRANCH_FEE,
    )
