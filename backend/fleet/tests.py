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
    Maintenance,
    Motorcycle,
    UtilityVehicle,
    Vehicle,
)
from fleet.services import InspectionService, VehicleService
from rentals.models import Rental, Reservation
from django.utils import timezone


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

    def test_rental_terms_use_vehicle_values_and_requirements(self):
        terms = self.service.get_rental_terms(self.vehicle.pk)

        self.assertEqual(terms.daily_rate, Decimal('999.00'))
        self.assertEqual(terms.minimum_deposit, Decimal('999.00'))
        self.assertEqual(terms.required_license_category, 'B')
        self.assertEqual(terms.minimum_age, 21)
        self.assertEqual(terms.status, Vehicle.Status.AVAILABLE)

    def test_vehicle_model_exposes_its_rental_terms(self):
        terms = self.vehicle.get_rental_terms()

        self.assertEqual(terms.daily_rate, Decimal('999.00'))
        self.assertEqual(terms.minimum_deposit, Decimal('999.00'))
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

    def test_entry_inspection_flags_damage_and_sends_vehicle_to_maintenance(self):
        branch = Branch.objects.create(
            name='Norte',
            address='Rua Um, 10',
            city='Campinas',
            state='SP',
        )
        vehicle = Car.objects.create(
            plate='DEF4G56',
            model='Hatch',
            year=2025,
            branch=branch,
        )
        now = timezone.now()
        reservation = Reservation.objects.create(
            customer_id=1,
            vehicle_id=vehicle.pk,
            pickup_branch_id=branch.pk,
            return_branch_id=branch.pk,
            starts_at=now,
            expected_return_at=now + timezone.timedelta(days=1),
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('120.00'),
            first_day_amount_snapshot=Decimal('120.00'),
        )
        rental = Rental.objects.create(reservation=reservation)

        inspection = InspectionService().register(
            rental.pk,
            Inspection.InspectionType.ENTRY,
            1200,
            Decimal('250.00'),
            'Risco na porta',
        )

        vehicle.refresh_from_db()
        maintenance = Maintenance.objects.get(vehicle=vehicle)
        self.assertTrue(inspection.has_damage)
        self.assertEqual(vehicle.status, Vehicle.Status.MAINTENANCE)
        self.assertEqual(vehicle.mileage, 1200)
        self.assertEqual(maintenance.reason, 'Risco na porta')


class FleetManagementApiTests(APITestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Leste',
            address='Rua Dois, 20',
            city='Santos',
            state='SP',
        )

    def test_availability_only_returns_available_vehicles_without_period_conflicts(self):
        now = timezone.now()
        starts_at = now + timezone.timedelta(days=2)
        expected_return_at = starts_at + timezone.timedelta(days=3)
        reserved = Car.objects.create(
            plate='GHI7J89',
            model='Sedan',
            year=2025,
            branch=self.branch,
        )
        available = Car.objects.create(
            plate='KLM1N23',
            model='Wagon',
            year=2025,
            branch=self.branch,
        )
        unavailable = Car.objects.create(
            plate='PQR4S56',
            model='SUV',
            year=2025,
            status=Vehicle.Status.MAINTENANCE,
            branch=self.branch,
        )
        Reservation.objects.create(
            customer_id=1,
            vehicle_id=reserved.pk,
            pickup_branch_id=self.branch.pk,
            return_branch_id=self.branch.pk,
            starts_at=starts_at,
            expected_return_at=expected_return_at,
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('360.00'),
            first_day_amount_snapshot=Decimal('120.00'),
        )

        response = self.client.get(
            '/api/fleet/availability',
            {
                'starts_at': starts_at.isoformat(),
                'expected_return_at': expected_return_at.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['results']], [available.pk])
        self.assertNotIn(unavailable.pk, [item['id'] for item in response.data['results']])

    def test_vehicle_crud_creates_subtype_and_updates_vehicle(self):
        response = self.client.post(
            '/api/fleet/vehicles',
            {
                'vehicle_type': 'CAR',
                'plate': 'TUV7W89',
                'model': 'Compacto',
                'year': 2026,
                'branch': self.branch.pk,
                'doors': 2,
                'trunk_capacity_liters': 250,
                'daily_rate': '95.00',
                'deposit_amount': '200.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        vehicle_id = response.data['id']
        self.assertEqual(response.data['doors'], 2)
        self.assertEqual(response.data['daily_rate'], '95.00')
        update = self.client.patch(
            f'/api/fleet/vehicles/{vehicle_id}',
            {'model': 'Compacto atualizado'},
            format='json',
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['model'], 'Compacto atualizado')
        self.assertEqual(self.client.delete(f'/api/fleet/vehicles/{vehicle_id}').status_code, 204)

    def test_branch_crud(self):
        response = self.client.post(
            '/api/fleet/branches',
            {
                'name': 'Oeste',
                'address': 'Rua Três, 30',
                'city': 'Jundiaí',
                'state': 'SP',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        branch_id = response.data['id']
        update = self.client.patch(
            f'/api/fleet/branches/{branch_id}',
            {'city': 'Louveira'},
            format='json',
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data['city'], 'Louveira')
        self.assertEqual(self.client.delete(f'/api/fleet/branches/{branch_id}').status_code, 204)

    def test_inspection_registration_updates_vehicle_and_records_damage(self):
        vehicle = Car.objects.create(
            plate='XYZ8A90',
            model='Hatch',
            year=2025,
            branch=self.branch,
        )
        now = timezone.now()
        reservation = Reservation.objects.create(
            customer_id=1,
            vehicle_id=vehicle.pk,
            pickup_branch_id=self.branch.pk,
            return_branch_id=self.branch.pk,
            starts_at=now,
            expected_return_at=now + timezone.timedelta(days=1),
            daily_rate_snapshot=Decimal('120.00'),
            quoted_total=Decimal('120.00'),
            first_day_amount_snapshot=Decimal('120.00'),
        )
        rental = Rental.objects.create(reservation=reservation)

        response = self.client.post(
            '/api/fleet/inspections',
            {
                'rental_id': rental.pk,
                'inspection_type': Inspection.InspectionType.ENTRY,
                'mileage': 1250,
                'damages': '250.00',
                'damage_description': 'Risco na porta',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['has_damage'])
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, Vehicle.Status.MAINTENANCE)
        self.assertEqual(vehicle.mileage, 1250)

    def test_maintenance_can_be_started_and_released(self):
        vehicle = Car.objects.create(
            plate='UVW3X45',
            model='Utilitário',
            year=2025,
            branch=self.branch,
        )

        response = self.client.post(
            '/api/fleet/maintenance',
            {
                'vehicle_id': vehicle.pk,
                'reason': 'Revisão programada',
                'mileage': 5000,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        maintenance_id = response.data['id']
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, Vehicle.Status.MAINTENANCE)
        self.assertEqual(vehicle.mileage, 5000)

        released = self.client.post(f'/api/fleet/maintenance/{maintenance_id}/release')

        self.assertEqual(released.status_code, 200)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, Vehicle.Status.AVAILABLE)
        self.assertIsNotNone(released.data['completed_at'])


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
