from datetime import datetime
from decimal import Decimal

from customers.models import Customer, Insurance


class CustomerService:
    def validate_eligibility(
        self,
        customer_id: int,
        required_category: str,
        minimum_age: int,
        start: datetime,
        end: datetime,
    ) -> bool:
        return True

    def register_completed_rental(self, customer_id: int) -> None:
        customer = Customer.objects.get(pk=customer_id)
        customer.completed_rentals += 1
        customer.save(update_fields=("completed_rentals",))


class QuoteService:
    def calculate(
        self,
        daily_rate: Decimal,
        insurance_id: int | None,
        customer_id: int,
        days: int,
    ) -> Decimal:
        insurance_cost = Decimal("0.00")
        if insurance_id is not None:
            insurance = Insurance.objects.get(pk=insurance_id).get_real()
            insurance_cost = insurance.calculate_daily_cost()
        return (daily_rate + insurance_cost) * days
