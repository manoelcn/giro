from datetime import date
from decimal import Decimal

from django.apps import apps
from django.contrib import admin
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

from customers.models import BasicInsurance, Customer, FullInsurance
from accounts.models import Employee
from fleet.models import (
    Branch,
    Car,
    Inspection,
    Motorcycle,
    UtilityVehicle,
    Vehicle,
)
from fleet.services import InspectionService, VehicleService


class VehicleServiceTests(TestCase):
    def setUp(self):
        branch = Branch.objects.create(
            name='Centro',
            address='Rua Central, 1',
            city='São Paulo',
            state='SP',
        )
        self.vehicle = Car.objects.create(
            plate='ABC1D23',
            model='Sedan',
            year=2024,
            required_license_category=Vehicle.LicenseCategory.B,
            minimum_driver_age=21,
            daily_rate=Decimal('999.00'),
            deposit_amount=Decimal('999.00'),
            branch=branch,
            doors=4,
            trunk_capacity_liters=400,
        )
        self.service = VehicleService()

    def test_rental_terms_use_fixed_values_and_vehicle_requirements(self):
        terms = self.service.get_rental_terms(self.vehicle.pk)

        self.assertEqual(terms.daily_rate, Decimal('120.00'))
        self.assertEqual(terms.minimum_deposit, Decimal('300.00'))
        self.assertEqual(terms.required_license_category, 'B')
        self.assertEqual(terms.minimum_age, 21)
        self.assertEqual(terms.status, Vehicle.Status.AVAILABLE)

    def test_vehicle_status_contract_methods_update_persisted_status(self):
        self.service.mark_reserved(self.vehicle.pk)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.RESERVED)

        self.service.mark_rented(self.vehicle.pk)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.RENTED)

        self.service.release(self.vehicle.pk)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, Vehicle.Status.AVAILABLE)


class InspectionServiceTests(TestCase):
    def test_register_and_get_inspection(self):
        service = InspectionService()
        self.assertIsNone(service.get(42, Inspection.InspectionType.EXIT))

        saved = service.register(42, Inspection.InspectionType.EXIT, 1200, Decimal('250.00'))

        result = service.get(42, Inspection.InspectionType.EXIT)
        self.assertEqual(result.pk, saved.pk)
        self.assertEqual(result.mileage, 1200)
        self.assertEqual(result.damages, Decimal('250.00'))


class BaseSeedCommandTests(APITestCase):
    def test_seed_base_is_idempotent_and_creates_requested_sample_counts(self):
        call_command('seed_base', verbosity=0)
        call_command('seed_base', verbosity=0)

        self.assertEqual(Branch.objects.count(), 2)
        self.assertEqual(Car.objects.count(), 2)
        self.assertEqual(Motorcycle.objects.count(), 2)
        self.assertEqual(UtilityVehicle.objects.count(), 2)
        self.assertEqual(Customer.objects.count(), 4)
        self.assertEqual(BasicInsurance.objects.count(), 1)
        self.assertEqual(FullInsurance.objects.count(), 1)
        self.assertEqual(Employee.objects.count(), 3)

        vehicle_results = self.client.get('/api/fleet/vehicles').data['results']
        self.assertEqual(len(vehicle_results), 6)
        self.assertEqual(
            {vehicle['vehicle_type'] for vehicle in vehicle_results},
            {'CAR', 'MOTORCYCLE', 'UTILITYVEHICLE'},
        )


class BaseCatalogApiTests(APITestCase):
    def setUp(self):
        branch = Branch.objects.create(
            name='Centro',
            address='Rua Central, 1',
            city='São Paulo',
            state='SP',
        )
        Car.objects.create(
            plate='ABC1D23',
            model='Sedan',
            year=2024,
            branch=branch,
            daily_rate=Decimal('120.00'),
            deposit_amount=Decimal('300.00'),
        )
        Customer.objects.create(
            full_name='Ana Silva',
            national_id='11111111111',
            email='ana@example.test',
            phone='11990000000',
            birth_date=date(1990, 5, 10),
        )
        BasicInsurance.objects.create(
            name='Básico',
            daily_cost=Decimal('25.00'),
            deductible=Decimal('3000.00'),
            coverage_limit=Decimal('5000.00'),
        )

    def test_all_base_models_are_registered_in_admin(self):
        for app_label in ('fleet', 'customers', 'accounts', 'finance'):
            for model in apps.get_app_config(app_label).get_models():
                self.assertTrue(admin.site.is_registered(model), model.__name__)

    def test_catalog_lists_are_open_read_only_and_have_standard_envelope(self):
        paths = (
            '/api/fleet/vehicles',
            '/api/fleet/branches',
            '/api/customers/customers',
            '/api/customers/insurances',
        )
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.data['count'], 1, path)
            self.assertIsNone(response.data['next'], path)
            self.assertEqual(len(response.data['results']), 1, path)
            self.assertEqual(
                self.client.post(path, {}, format='json').status_code,
                405,
                path,
            )

        vehicle = self.client.get('/api/fleet/vehicles').data['results'][0]
        self.assertEqual(vehicle['vehicle_type'], 'CAR')
        self.assertEqual(vehicle['doors'], 4)

    def test_existing_rental_api_remains_authenticated(self):
        response = self.client.get('/api/rentals')

        self.assertEqual(response.status_code, 403)
