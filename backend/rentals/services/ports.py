from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class RentalTerms:
    daily_rate: Decimal
    minimum_deposit: Decimal
    operational: bool


@dataclass(frozen=True)
class Quote:
    daily_rate: Decimal
    first_day_amount: Decimal
    quoted_total: Decimal


@dataclass(frozen=True)
class Inspection:
    inspection_id: int
    inspection_type: str
    has_damage: bool = False


class VehicleService(Protocol):
    def get_rental_terms(self, vehicle_id: int) -> RentalTerms: ...

    def mark_rented(self, vehicle_id: int) -> None: ...

    def release(self, vehicle_id: int) -> None: ...

    def available_equivalents(
        self,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
    ) -> list[int]: ...


class InspectionService(Protocol):
    def get(self, rental_id: int, inspection_type: str) -> Inspection | None: ...


class CustomerService(Protocol):
    def validate_eligibility(self, customer_id: int) -> bool: ...


class QuoteService(Protocol):
    def calculate(
        self,
        *,
        customer_id: int,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
        pickup_branch_id: int,
        return_branch_id: int,
        insurance_id: int | None,
    ) -> Quote: ...


class InsuranceService(Protocol):
    def calculate_customer_damage_cost(
        self,
        customer_id: int,
        inspection: Inspection,
    ) -> Decimal: ...


class PaymentService(Protocol):
    def is_deposit_paid(self, rental_id: int, minimum_amount: Decimal) -> bool: ...

    def create_pending_charge(
        self,
        rental_id: int,
        customer_id: int,
        charge_type: str,
        amount: Decimal,
    ) -> int: ...

    def close_deposit(self, rental_id: int, amount_due: Decimal) -> Decimal: ...


class FineService(Protocol):
    def create(
        self,
        rental_id: int,
        customer_id: int,
        fine_type: str,
        amount: Decimal,
    ) -> int: ...


class FinanceQuery(Protocol):
    def balance_due(self, rental_id: int) -> Decimal: ...


class AccountAccess(Protocol):
    def can_operate_in_branch(self, actor_id: int, branch_id: int) -> bool: ...
