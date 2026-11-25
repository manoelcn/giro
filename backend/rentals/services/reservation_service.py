from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import OperationalError, transaction
from django.utils import timezone

from core.domain.exceptions import GiroException
from core.domain.money import to_money
from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import (
    CancellationDeadlineExceededException,
    ConflictingReservationException,
    DatabaseContentionException,
    IntegrationNotConfiguredException,
    InvalidStateTransitionException,
    QuoteChangedException,
    ReservationNotFoundException,
    VehicleUnavailableException,
)
from rentals.models import Rental, Reservation
from rentals.repositories.reservation_repository import ReservationRepository
from rentals.domain.rental import Rental as RentalState
from rentals.domain.reservation import Reservation as ReservationState
from rentals.services.ports import PaymentService, Quote, QuoteService, RentalTerms, VehicleService


@dataclass(frozen=True)
class CancellationCharge:
    id: int
    amount: Decimal
    status: str = 'PENDING'


@dataclass(frozen=True)
class CancellationQuote:
    cancellation_charge: Decimal | None


@dataclass(frozen=True)
class ReservationCancellationResult:
    reservation: Reservation
    cancellation_charge: CancellationCharge | None


class ReservationService:
    def __init__(
        self,
        *,
        vehicle_service: VehicleService,
        quote_service: QuoteService,
        payment_service: PaymentService | None = None,
        repository: ReservationRepository | None = None,
    ) -> None:
        self.vehicle_service = vehicle_service
        self.quote_service = quote_service
        self.payment_service = payment_service
        self.repository = repository or ReservationRepository()

    def quote(
        self,
        *,
        customer_id: int,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
        pickup_branch_id: int,
        return_branch_id: int,
        insurance_id: int | None,
    ) -> Quote:
        self._validate_period(starts_at, expected_return_at)
        _, quote = self._get_quote(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            starts_at=starts_at,
            expected_return_at=expected_return_at,
            pickup_branch_id=pickup_branch_id,
            return_branch_id=return_branch_id,
            insurance_id=insurance_id,
        )
        return Quote(
            daily_rate=to_money(quote.daily_rate),
            first_day_amount=to_money(quote.first_day_amount),
            quoted_total=to_money(quote.quoted_total),
        )

    def create(
        self,
        *,
        customer_id: int,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
        pickup_branch_id: int,
        return_branch_id: int,
        insurance_id: int | None,
        accepted_total: Decimal | int | str,
    ) -> tuple[Reservation, Rental]:
        self._validate_period(starts_at, expected_return_at)
        try:
            with transaction.atomic():
                terms, quote = self._get_quote(
                    customer_id=customer_id,
                    vehicle_id=vehicle_id,
                    starts_at=starts_at,
                    expected_return_at=expected_return_at,
                    pickup_branch_id=pickup_branch_id,
                    return_branch_id=return_branch_id,
                    insurance_id=insurance_id,
                )
                if to_money(accepted_total) != to_money(quote.quoted_total):
                    raise QuoteChangedException()
                if self.repository.has_conflict(
                    vehicle_id,
                    starts_at,
                    expected_return_at,
                ):
                    raise ConflictingReservationException()

                reservation = self.repository.create(
                    customer_id=customer_id,
                    vehicle_id=vehicle_id,
                    pickup_branch_id=pickup_branch_id,
                    return_branch_id=return_branch_id,
                    insurance_id=insurance_id,
                    starts_at=starts_at,
                    expected_return_at=expected_return_at,
                    status=ReservationStatus.CONFIRMED,
                    daily_rate_snapshot=to_money(quote.daily_rate),
                    quoted_total=to_money(quote.quoted_total),
                    first_day_amount_snapshot=to_money(quote.first_day_amount),
                )
                rental = Rental.objects.create(
                    reservation=reservation,
                    status=RentalStatus.RESERVED,
                    deposit_required_snapshot=to_money(terms.minimum_deposit),
                )
                return reservation, rental
        except OperationalError as exc:
            if 'locked' in str(exc).lower() or 'busy' in str(exc).lower():
                raise DatabaseContentionException() from exc
            raise

    def cancellation_quote(
        self,
        reservation_id: int,
        *,
        now: datetime | None = None,
    ) -> CancellationQuote:
        reservation = self.repository.get(reservation_id)
        if reservation is None:
            raise ReservationNotFoundException()
        cancellation_at = now or timezone.now()
        self._validate_cancellable(reservation, cancellation_at)
        amount = self._cancellation_amount(reservation, cancellation_at)
        return CancellationQuote(cancellation_charge=amount)

    def cancel(
        self,
        reservation_id: int,
        *,
        now: datetime | None = None,
    ) -> ReservationCancellationResult:
        cancellation_at = now or timezone.now()
        with transaction.atomic():
            reservation = self.repository.get(reservation_id)
            if reservation is None:
                raise ReservationNotFoundException()
            self._validate_cancellable(reservation, cancellation_at)
            rental = reservation.rental
            reservation_state = self._reservation_state(reservation)
            rental_state = self._rental_state(rental)
            reservation_state.transition_to(ReservationStatus.CANCELED)
            rental_state.transition_to(RentalStatus.CANCELED)

            amount = self._cancellation_amount(reservation, cancellation_at)
            cancellation_charge = None
            if amount is not None:
                if self.payment_service is None:
                    raise IntegrationNotConfiguredException()
                charge_id = self.payment_service.create_pending_charge(
                    rental.pk,
                    reservation.customer_id,
                    'CANCELLATION',
                    amount,
                )
                rental.cancellation_charge_id = charge_id
                cancellation_charge = CancellationCharge(
                    id=charge_id,
                    amount=amount,
                )

            reservation.status = reservation_state.status
            reservation.canceled_at = cancellation_at
            rental.status = rental_state.status
            reservation.save(update_fields=['status', 'canceled_at'])
            rental.save(
                update_fields=['status', 'cancellation_charge_id', 'updated_at']
            )
            return ReservationCancellationResult(
                reservation=reservation,
                cancellation_charge=cancellation_charge,
            )

    @staticmethod
    def _reservation_state(reservation: Reservation) -> ReservationState:
        return ReservationState(
            customer_id=reservation.customer_id,
            vehicle_id=reservation.vehicle_id,
            starts_at=reservation.starts_at,
            expected_return_at=reservation.expected_return_at,
            status=ReservationStatus(reservation.status),
        )

    @staticmethod
    def _rental_state(rental: Rental) -> RentalState:
        return RentalState(
            reservation_id=rental.reservation_id,
            status=RentalStatus(rental.status),
        )

    @staticmethod
    def _validate_cancellable(reservation: Reservation, now: datetime) -> None:
        if reservation.status == ReservationStatus.FULFILLED:
            raise CancellationDeadlineExceededException()
        if reservation.status != ReservationStatus.CONFIRMED:
            raise InvalidStateTransitionException()
        try:
            rental = reservation.rental
        except Rental.DoesNotExist as exc:
            raise InvalidStateTransitionException() from exc
        if rental.status != RentalStatus.RESERVED:
            if rental.status in (RentalStatus.PICKED_UP, RentalStatus.OVERDUE):
                raise CancellationDeadlineExceededException()
            raise InvalidStateTransitionException()
        if now >= reservation.starts_at:
            raise CancellationDeadlineExceededException(
                'O prazo de cancelamento terminou; a retirada já deveria ter ocorrido.'
            )

    @staticmethod
    def _cancellation_amount(
        reservation: Reservation,
        now: datetime,
    ) -> Decimal | None:
        if reservation.starts_at - now >= timedelta(hours=24):
            return None
        return to_money(reservation.first_day_amount_snapshot * Decimal('0.20'))

    def _get_quote(
        self,
        *,
        customer_id: int,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
        pickup_branch_id: int,
        return_branch_id: int,
        insurance_id: int | None,
    ) -> tuple[RentalTerms, Quote]:
        terms = self.vehicle_service.get_rental_terms(vehicle_id)
        if not terms.operational:
            raise VehicleUnavailableException()
        quote = self.quote_service.calculate(
            customer_id=customer_id,
            vehicle_id=vehicle_id,
            starts_at=starts_at,
            expected_return_at=expected_return_at,
            pickup_branch_id=pickup_branch_id,
            return_branch_id=return_branch_id,
            insurance_id=insurance_id,
        )
        return terms, quote

    @staticmethod
    def _validate_period(starts_at: datetime, expected_return_at: datetime) -> None:
        if expected_return_at <= starts_at:
            raise GiroException(
                'A devolução prevista deve ser posterior à retirada.',
                fields={'expected_return_at': 'Informe um período válido.'},
            )
