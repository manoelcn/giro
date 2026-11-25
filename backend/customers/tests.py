from datetime import date
from decimal import Decimal

from django.test import TestCase

from customers.models import BasicInsurance, Customer
from customers.services import CustomerService, InsuranceService, QuoteService


class CustomerServicesTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name='Ana Silva',
            national_id='11111111111',
            email='ana@example.test',
            phone='11990000000',
            birth_date=date(1990, 5, 10),
        )
        self.insurance = BasicInsurance.objects.create(
            name='Básico',
            daily_cost=Decimal('25.00'),
            deductible=Decimal('3000.00'),
            coverage_limit=Decimal('5000.00'),
        )

    def test_eligibility_contract_does_not_block(self):
        eligible = CustomerService().validate_eligibility(
            customer_id=self.customer.pk,
            required_category='C',
            minimum_age=99,
            start=date(2030, 1, 1),
            end=date(2030, 1, 4),
        )

        self.assertTrue(eligible)

    def test_quote_includes_selected_insurance_daily_cost(self):
        total = QuoteService().calculate(
            Decimal('120.00'),
            self.insurance.pk,
            self.customer.pk,
            3,
        )

        self.assertEqual(total, Decimal('435.00'))

    def test_completed_rental_increments_customer_counter(self):
        CustomerService().register_completed_rental(self.customer.pk)
        self.customer.refresh_from_db()

        self.assertEqual(self.customer.completed_rentals, 1)

    def test_insurance_damage_cost_is_capped_by_deductible(self):
        amount = InsuranceService().calculate_customer_damage_cost(
            self.insurance.pk,
            Decimal('4500.00'),
        )

        self.assertEqual(amount, Decimal('3000.00'))
