from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from rentals.services.ports import Inspection, Quote, RentalTerms


class _FaultInjectable:
    def __init__(self) -> None:
        self.fail_on: set[str] = set()

    def _raise_if_configured(self, operation: str) -> None:
        if operation in self.fail_on:
            raise RuntimeError(f'Injected failure: {operation}')


class FakeVehicleService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.terms: dict[int, RentalTerms] = {}
        self.rented_vehicle_ids: set[int] = set()
        self.equivalent_vehicle_ids: dict[int, list[int]] = {}

    def get_rental_terms(self, vehicle_id: int) -> RentalTerms:
        self._raise_if_configured('get_rental_terms')
        return self.terms[vehicle_id]

    def mark_rented(self, vehicle_id: int) -> None:
        self._raise_if_configured('mark_rented')
        transaction.on_commit(lambda: self.rented_vehicle_ids.add(vehicle_id))

    def release(self, vehicle_id: int) -> None:
        self._raise_if_configured('release')
        transaction.on_commit(lambda: self.rented_vehicle_ids.discard(vehicle_id))

    def available_equivalents(
        self,
        vehicle_id: int,
        starts_at: datetime,
        expected_return_at: datetime,
    ) -> list[int]:
        self._raise_if_configured('available_equivalents')
        return self.equivalent_vehicle_ids.get(vehicle_id, []).copy()


class FakeInspectionService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.inspections: dict[tuple[int, str], Inspection] = {}

    def get(self, rental_id: int, inspection_type: str) -> Inspection | None:
        self._raise_if_configured('get')
        return self.inspections.get((rental_id, inspection_type))


class FakeCustomerService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.ineligible_customer_ids: set[int] = set()

    def validate_eligibility(self, customer_id: int) -> bool:
        self._raise_if_configured('validate_eligibility')
        return customer_id not in self.ineligible_customer_ids


class FakeQuoteService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.result: Quote | None = None

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
    ) -> Quote:
        self._raise_if_configured('calculate')
        if self.result is None:
            raise LookupError('Configure FakeQuoteService.result before quoting.')
        return self.result


class FakeInsuranceService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.damage_costs: dict[int, Decimal] = {}

    def calculate_customer_damage_cost(
        self,
        customer_id: int,
        inspection: Inspection,
    ) -> Decimal:
        self._raise_if_configured('calculate_customer_damage_cost')
        return self.damage_costs.get(inspection.inspection_id, Decimal('0.00'))


class FakeFinanceService(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.charges: list[tuple[int, int, str, Decimal]] = []
        self.deposits: dict[int, Decimal] = defaultdict(lambda: Decimal('0.00'))
        self.balances_due: dict[int, Decimal] = defaultdict(lambda: Decimal('0.00'))
        self.released_deposits: dict[int, Decimal] = defaultdict(lambda: Decimal('0.00'))
        self._next_charge_id = 1

    def is_deposit_paid(self, rental_id: int, minimum_amount: Decimal) -> bool:
        self._raise_if_configured('is_deposit_paid')
        return self.deposits[rental_id] >= minimum_amount

    def create_pending_charge(
        self,
        rental_id: int,
        customer_id: int,
        charge_type: str,
        amount: Decimal,
    ) -> int:
        self._raise_if_configured('create_pending_charge')
        charge_id = self._next_charge_id
        self._next_charge_id += 1

        def persist_charge() -> None:
            self.charges.append((rental_id, customer_id, charge_type, amount))
            self.balances_due[rental_id] += amount

        transaction.on_commit(persist_charge)
        return charge_id

    def create(
        self,
        rental_id: int,
        customer_id: int,
        fine_type: str,
        amount: Decimal,
    ) -> int:
        self._raise_if_configured('create')
        return self.create_pending_charge(rental_id, customer_id, fine_type, amount)

    def balance_due(self, rental_id: int) -> Decimal:
        self._raise_if_configured('balance_due')
        return self.balances_due[rental_id]

    def close_deposit(self, rental_id: int, amount_due: Decimal) -> Decimal:
        self._raise_if_configured('close_deposit')
        deposit = self.deposits[rental_id]
        applied = min(deposit, amount_due)
        remaining_deposit = deposit - applied
        balance_after_deposit = amount_due - applied

        def persist_deposit_closeout() -> None:
            self.deposits[rental_id] = remaining_deposit
            self.balances_due[rental_id] = balance_after_deposit
            if balance_after_deposit == Decimal('0.00'):
                self.released_deposits[rental_id] += remaining_deposit
                self.deposits[rental_id] = Decimal('0.00')

        transaction.on_commit(persist_deposit_closeout)
        return balance_after_deposit


class FakeAccountAccess(_FaultInjectable):
    def __init__(self) -> None:
        super().__init__()
        self.denied_branches: set[tuple[int, int]] = set()

    def can_operate_in_branch(self, actor_id: int, branch_id: int) -> bool:
        self._raise_if_configured('can_operate_in_branch')
        return (actor_id, branch_id) not in self.denied_branches
