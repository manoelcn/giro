from datetime import date
from decimal import Decimal

from django.test import TestCase

from customers.models import BasicInsurance, Customer, FullInsurance, Insurance
from customers.services import CustomerService, InsuranceService, QuoteService


class CustomerServicesTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            full_name="Ana Silva",
            national_id="11111111111",
            email="ana@example.test",
            phone="11990000000",
            birth_date=date(1990, 5, 10),
        )
        self.insurance = BasicInsurance.objects.create(
            name="Básico",
            daily_cost=Decimal("25.00"),
            deductible=Decimal("3000.00"),
            coverage_limit=Decimal("5000.00"),
        )

    def test_eligibility_contract_does_not_block(self):
        eligible = CustomerService().validate_eligibility(
            customer_id=self.customer.pk,
            required_category="C",
            minimum_age=99,
            start=date(2030, 1, 1),
            end=date(2030, 1, 4),
        )

        self.assertTrue(eligible)

    def test_quote_includes_selected_insurance_daily_cost(self):
        total = QuoteService().calculate(
            Decimal("120.00"),
            self.insurance.pk,
            self.customer.pk,
            3,
        )

        self.assertEqual(total, Decimal("435.00"))

    def test_completed_rental_increments_customer_counter(self):
        CustomerService().register_completed_rental(self.customer.pk)
        self.customer.refresh_from_db()

        self.assertEqual(self.customer.completed_rentals, 1)

    def test_service_uses_the_rule_of_the_insurance_type(self):
        amount = InsuranceService().calculate_customer_damage_cost(
            self.insurance.pk,
            Decimal("4500.00"),
        )

        self.assertEqual(amount, Decimal("3600.00"))


class InsurancePolymorphismTests(TestCase):
    def setUp(self):
        self.basic = BasicInsurance.objects.create(
            name="Básico",
            daily_cost=Decimal("25.00"),
            deductible=Decimal("3000.00"),
            coverage_limit=Decimal("5000.00"),
        )
        self.full = FullInsurance.objects.create(
            name="Completo",
            daily_cost=Decimal("45.00"),
            deductible=Decimal("1000.00"),
            coverage_limit=Decimal("50000.00"),
            third_party_coverage=True,
            roadside_assistance=True,
        )

    def test_basic_passes_most_of_the_damage_to_the_customer(self):
        self.assertEqual(
            self.basic.calculate_customer_damage_cost(Decimal("4500.00")),
            Decimal("3600.00"),
        )

    def test_full_limits_the_customer_to_the_deductible(self):
        self.assertEqual(
            self.full.calculate_customer_damage_cost(Decimal("4500.00")),
            Decimal("1000.00"),
        )

    def test_full_charges_the_whole_damage_when_below_the_deductible(self):
        self.assertEqual(
            self.full.calculate_customer_damage_cost(Decimal("300.00")),
            Decimal("300.00"),
        )

    def test_same_call_gives_different_results_per_type(self):
        damage = Decimal("2000.00")
        results = {
            insurance.name: insurance.calculate_customer_damage_cost(damage)
            for insurance in (self.basic, self.full)
        }

        self.assertEqual(results["Básico"], Decimal("1600.00"))
        self.assertEqual(results["Completo"], Decimal("1000.00"))

    def test_get_real_returns_the_child_class_from_the_base_query(self):
        base_objects = Insurance.objects.order_by("name")

        real_types = [insurance.get_real().__class__ for insurance in base_objects]

        self.assertEqual(real_types, [BasicInsurance, FullInsurance])

    def test_base_class_does_not_define_the_damage_rule(self):
        base = Insurance.objects.create(name="Genérico")

        with self.assertRaises(NotImplementedError):
            base.calculate_customer_damage_cost(Decimal("100.00"))

    def test_basic_has_its_own_member_with_default_percentage(self):
        self.assertEqual(self.basic.customer_share_percent, Decimal("80.00"))

    def test_full_has_its_own_members(self):
        self.assertTrue(self.full.third_party_coverage)
        self.assertTrue(self.full.roadside_assistance)
