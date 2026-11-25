from decimal import Decimal

from django.test import TestCase

from finance.models import Fine, Payment
from finance.services import FinanceQuery, FineService, PaymentService


class FinanceServicesTests(TestCase):
    def test_deposit_contract_and_settlement_create_payments(self):
        service = PaymentService()
        deposit = service.register_deposit(12, Decimal('300.00'), Payment.Method.CARD)
        settlement = service.settle(12, Decimal('120.00'), Payment.Method.PIX)

        self.assertTrue(service.is_deposit_paid(12, Decimal('300.00')))
        self.assertTrue(deposit.is_deposit)
        self.assertEqual(deposit.status, Payment.Status.SETTLED)
        self.assertEqual(settlement.amount, Decimal('120.00'))
        self.assertEqual(Payment.objects.count(), 2)

    def test_fine_creation_and_pending_query_contract(self):
        fine = FineService().create(12, 41, Fine.FineType.LATE, Decimal('79.99'))

        self.assertEqual(fine.status, Fine.Status.PENDING)
        self.assertFalse(FinanceQuery().customer_has_pending(41))
