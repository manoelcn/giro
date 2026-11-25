from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.domain.money import to_money
from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.domain.exceptions import (
    CustomerIneligibleException,
    IntegrationNotConfiguredException,
    InsufficientDepositException,
    InvalidStateTransitionException,
    PendingBalanceException,
    PendingInspectionException,
    RentalNotFoundException,
)
from rentals.domain.rental import Rental as RentalState
from rentals.domain.reservation import Reservation as ReservationState
from rentals.models import Rental as RentalModel
from rentals.models import Reservation
from rentals.repositories.rental_repository import RentalRepository
from rentals.services.ports import (
    CustomerService,
    FinanceQuery,
    FineService,
    InspectionService,
    InsuranceService,
    PaymentService,
    VehicleService,
)


@dataclass(frozen=True)
class RentalReturnResult:
    rental: RentalModel
    late_day_count: int
    late_charge_amount: Decimal
    inter_branch_charge_amount: Decimal
    damage_charge_amount: Decimal
    balance_due: Decimal


@dataclass(frozen=True)
class OverdueAlert:
    rental_id: int
    affected_reservation_id: int
    equivalent_vehicle_ids: list[int]


class RentalService:
    def __init__(
        self,
        *,
        vehicle_service: VehicleService,
        inspection_service: InspectionService,
        customer_service: CustomerService,
        payment_service: PaymentService,
        fine_service: FineService | None = None,
        finance_query: FinanceQuery | None = None,
        insurance_service: InsuranceService | None = None,
        inter_branch_fee: Decimal | None = None,
        repository: RentalRepository | None = None,
    ) -> None:
        self.vehicle_service = vehicle_service
        self.inspection_service = inspection_service
        self.customer_service = customer_service
        self.payment_service = payment_service
        self.fine_service = fine_service
        self.finance_query = finance_query
        self.insurance_service = insurance_service
        self.inter_branch_fee = to_money(
            inter_branch_fee
            if inter_branch_fee is not None
            else settings.RENTALS_INTER_BRANCH_FEE
        )
        self.repository = repository or RentalRepository()

    def pick_up(
        self,
        rental_id: int,
        *,
        inspection_id: int,
        now: datetime | None = None,
    ) -> RentalModel:
        with transaction.atomic():
            rental = self.repository.get(rental_id)
            if rental is None:
                raise RentalNotFoundException()

            rental_state = RentalState(
                reservation_id=rental.reservation_id,
                status=RentalStatus(rental.status),
            )
            rental_state.transition_to(RentalStatus.PICKED_UP)

            reservation = rental.reservation
            reservation_state = ReservationState(
                customer_id=reservation.customer_id,
                vehicle_id=reservation.vehicle_id,
                starts_at=reservation.starts_at,
                expected_return_at=reservation.expected_return_at,
                status=ReservationStatus(reservation.status),
            )
            reservation_state.transition_to(ReservationStatus.FULFILLED)

            if not self.customer_service.validate_eligibility(reservation.customer_id):
                raise CustomerIneligibleException()

            inspection = self.inspection_service.get(rental.pk, 'EXIT')
            if inspection is None or inspection.inspection_id != inspection_id:
                raise PendingInspectionException()

            if not self.payment_service.is_deposit_paid(
                rental.pk,
                rental.deposit_required_snapshot,
            ):
                raise InsufficientDepositException(
                    f'A caução mínima exigida é R$ {rental.deposit_required_snapshot:.2f}.'
                )

            self.vehicle_service.mark_rented(reservation.vehicle_id)
            rental.status = rental_state.status
            rental.picked_up_at = now or timezone.now()
            reservation.status = reservation_state.status
            reservation.save(update_fields=['status'])
            rental.save(update_fields=['status', 'picked_up_at', 'updated_at'])
            return rental

    def return_vehicle(
        self,
        rental_id: int,
        *,
        inspection_id: int,
        return_branch_id: int,
        now: datetime | None = None,
    ) -> RentalReturnResult:
        if (
            self.fine_service is None
            or self.finance_query is None
            or self.insurance_service is None
        ):
            raise IntegrationNotConfiguredException()

        fine_service = self.fine_service
        finance_query = self.finance_query
        insurance_service = self.insurance_service
        returned_at = now or timezone.now()

        with transaction.atomic():
            rental = self.repository.get(rental_id)
            if rental is None:
                raise RentalNotFoundException()

            rental_state = RentalState(
                reservation_id=rental.reservation_id,
                status=RentalStatus(rental.status),
            )
            rental_state.transition_to(RentalStatus.RETURNED)

            reservation = rental.reservation
            inspection = self.inspection_service.get(rental.pk, 'ENTRY')
            if inspection is None or inspection.inspection_id != inspection_id:
                raise PendingInspectionException()

            late_day_count = self._late_day_count(
                reservation.expected_return_at,
                returned_at,
            )
            daily_rate = to_money(reservation.daily_rate_snapshot)
            late_charge_amount = to_money(
                daily_rate * Decimal('1.10') * late_day_count
            )
            inter_branch_charge_amount = (
                self.inter_branch_fee
                if return_branch_id != reservation.pickup_branch_id
                else Decimal('0.00')
            )
            damage_charge_amount = Decimal('0.00')
            if inspection.has_damage:
                damage_charge_amount = to_money(
                    insurance_service.calculate_customer_damage_cost(
                        reservation.customer_id,
                        inspection,
                    )
                )

            previous_balance = to_money(finance_query.balance_due(rental.pk))
            charge_amounts = {
                'RENTAL_BASE': to_money(reservation.quoted_total),
                'INTER_BRANCH_RETURN': inter_branch_charge_amount,
            }
            if charge_amounts['RENTAL_BASE'] > 0:
                self.payment_service.create_pending_charge(
                    rental.pk,
                    reservation.customer_id,
                    'RENTAL_BASE',
                    charge_amounts['RENTAL_BASE'],
                )
            if inter_branch_charge_amount > 0:
                self.payment_service.create_pending_charge(
                    rental.pk,
                    reservation.customer_id,
                    'INTER_BRANCH_RETURN',
                    inter_branch_charge_amount,
                )
            if late_charge_amount > 0:
                fine_service.create(
                    rental.pk,
                    reservation.customer_id,
                    'LATE',
                    late_charge_amount,
                )
            if damage_charge_amount > 0:
                fine_service.create(
                    rental.pk,
                    reservation.customer_id,
                    'DAMAGE',
                    damage_charge_amount,
                )

            self.vehicle_service.release(reservation.vehicle_id)
            rental.status = rental_state.status
            rental.returned_at = returned_at
            rental.actual_return_branch_id = return_branch_id
            rental.late_day_count = late_day_count
            rental.late_charge_amount = late_charge_amount
            rental.inter_branch_charge_amount = inter_branch_charge_amount
            rental.damage_charge_amount = damage_charge_amount
            rental.save(
                update_fields=[
                    'status',
                    'returned_at',
                    'actual_return_branch_id',
                    'late_day_count',
                    'late_charge_amount',
                    'inter_branch_charge_amount',
                    'damage_charge_amount',
                    'updated_at',
                ]
            )

            total_new_charges = (
                sum(charge_amounts.values(), Decimal('0.00'))
                + late_charge_amount
                + damage_charge_amount
            )
            return RentalReturnResult(
                rental=rental,
                late_day_count=late_day_count,
                late_charge_amount=late_charge_amount,
                inter_branch_charge_amount=inter_branch_charge_amount,
                damage_charge_amount=damage_charge_amount,
                balance_due=to_money(previous_balance + total_new_charges),
            )

    def finalize(self, rental_id: int, *, now: datetime | None = None) -> RentalModel:
        if self.finance_query is None:
            raise IntegrationNotConfiguredException()

        pending_balance: Decimal | None = None
        with transaction.atomic():
            rental = self.repository.get(rental_id)
            if rental is None:
                raise RentalNotFoundException()
            rental_state = RentalState(
                reservation_id=rental.reservation_id,
                status=RentalStatus(rental.status),
            )
            rental_state.transition_to(RentalStatus.COMPLETED)

            balance_due = to_money(self.finance_query.balance_due(rental.pk))
            balance_after_deposit = to_money(
                self.payment_service.close_deposit(rental.pk, balance_due)
            )
            if balance_after_deposit > 0:
                pending_balance = balance_after_deposit
            else:
                rental.status = rental_state.status
                rental.finalized_at = now or timezone.now()
                rental.save(update_fields=['status', 'finalized_at', 'updated_at'])

        if pending_balance is not None:
            raise PendingBalanceException(
                f'Saldo pendente de R$ {pending_balance:.2f}.',
                fields={'balance_due': format(pending_balance, '.2f')},
            )
        return rental

    def verify_overdue(self, now: datetime | None = None) -> list[OverdueAlert]:
        verification_time = now or timezone.now()
        threshold = verification_time - timedelta(hours=1)
        with transaction.atomic():
            candidates = self.repository.list().filter(
                status=RentalStatus.PICKED_UP,
                reservation__expected_return_at__lt=threshold,
            )
            for rental in candidates:
                rental_state = RentalState(
                    reservation_id=rental.reservation_id,
                    status=RentalStatus(rental.status),
                )
                rental_state.transition_to(RentalStatus.OVERDUE)
                rental.status = rental_state.status
                rental.save(update_fields=['status', 'updated_at'])
        return self.overdue_alerts(verification_time)

    def overdue_alerts(self, now: datetime | None = None) -> list[OverdueAlert]:
        verification_time = now or timezone.now()
        alerts = []
        overdue_rentals = self.repository.list().filter(status=RentalStatus.OVERDUE)
        for rental in overdue_rentals:
            reservation = rental.reservation
            affected_reservations = Reservation.objects.filter(
                vehicle_id=reservation.vehicle_id,
                status=ReservationStatus.CONFIRMED,
                starts_at__gt=max(verification_time, reservation.expected_return_at),
            ).exclude(pk=reservation.pk)
            for affected_reservation in affected_reservations:
                equivalent_vehicle_ids = self.vehicle_service.available_equivalents(
                    reservation.vehicle_id,
                    affected_reservation.starts_at,
                    affected_reservation.expected_return_at,
                )
                alerts.append(
                    OverdueAlert(
                        rental_id=rental.pk,
                        affected_reservation_id=affected_reservation.pk,
                        equivalent_vehicle_ids=equivalent_vehicle_ids,
                    )
                )
        return alerts

    @staticmethod
    def _late_day_count(expected_return_at: datetime, returned_at: datetime) -> int:
        grace_end = expected_return_at + timedelta(hours=1)
        if returned_at <= grace_end:
            return 0
        full_days, remainder = divmod(returned_at - grace_end, timedelta(days=1))
        return full_days + bool(remainder)
