from decimal import Decimal

from customers.models import Insurance


class InsuranceService:
    def calculate_customer_damage_cost(
        self,
        insurance_id: int,
        damage_value: Decimal,
    ) -> Decimal:
        insurance = Insurance.objects.get(pk=insurance_id).get_real()
        return insurance.calculate_customer_damage_cost(damage_value)
