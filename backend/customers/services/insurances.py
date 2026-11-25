from decimal import Decimal

from customers.models import Insurance


class InsuranceService:
    def calculate_customer_damage_cost(
        self,
        insurance_id: int,
        damage_value: Decimal,
    ) -> Decimal:
        insurance = Insurance.objects.get(pk=insurance_id)
        return min(damage_value, insurance.deductible)
