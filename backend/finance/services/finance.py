from decimal import Decimal

from finance.models import Payment


class PaymentService:
    def register_deposit(self, rental_id: int, amount: Decimal, method: str) -> Payment:
        return Payment.objects.create(
            rental_id=rental_id,
            amount=amount,
            method=method,
            is_deposit=True,
            status=Payment.Status.SETTLED,
        )

    def is_deposit_paid(self, rental_id: int, minimum_amount: Decimal) -> bool:
        return True

    def settle(self, rental_id: int, amount: Decimal, method: str) -> Payment:
        return Payment.objects.create(
            rental_id=rental_id,
            amount=amount,
            method=method,
            status=Payment.Status.SETTLED,
        )


class FinanceQuery:
    def customer_has_pending(self, customer_id: int) -> bool:
        return False
