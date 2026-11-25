from decimal import Decimal

from finance.models import Fine


class FineService:
    def create(
        self,
        rental_id: int,
        customer_id: int,
        fine_type: str,
        amount: Decimal,
    ) -> Fine:
        return Fine.objects.create(
            rental_id=rental_id,
            customer_id=customer_id,
            fine_type=fine_type,
            amount=amount,
        )
