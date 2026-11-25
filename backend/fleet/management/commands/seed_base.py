from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import Employee
from customers.models import BasicInsurance, Customer, DriverLicense, FullInsurance
from fleet.models import Branch, Car, Motorcycle, UtilityVehicle


class Command(BaseCommand):
    help = 'Create the initial sample data for the fleet, customers, and accounts modules.'

    def handle(self, *args, **options):
        branches = {}
        branch_data = (
            ('Centro', 'Rua Central, 100', 'São Paulo', 'SP'),
            ('Jardins', 'Av. Paulista, 500', 'São Paulo', 'SP'),
        )
        for name, address, city, state in branch_data:
            branch, _ = Branch.objects.update_or_create(
                name=name,
                defaults={'address': address, 'city': city, 'state': state},
            )
            branches[name] = branch

        vehicle_data = (
            (Car, 'ABC1D23', 'Sedan Compacto', 2023, 'B', 21, 'Centro', {'doors': 4, 'trunk_capacity_liters': 400}),
            (Car, 'ABC2D34', 'Hatch Compacto', 2022, 'B', 21, 'Jardins', {'doors': 4, 'trunk_capacity_liters': 300}),
            (Motorcycle, 'MOT1A23', 'Street 160', 2024, 'A', 21, 'Centro', {'displacement_cc': 160, 'helmet_included': True}),
            (Motorcycle, 'MOT2A34', 'Trail 250', 2023, 'A', 21, 'Jardins', {'displacement_cc': 250, 'helmet_included': True}),
            (UtilityVehicle, 'UTI1B23', 'Picape Leve', 2022, 'C', 25, 'Centro', {'load_capacity_kg': 750}),
            (UtilityVehicle, 'UTI2B34', 'Furgão Compacto', 2023, 'C', 25, 'Jardins', {'load_capacity_kg': 900}),
        )
        for (
            vehicle_model,
            plate,
            model,
            year,
            license_category,
            minimum_age,
            branch_name,
            specific_fields,
        ) in vehicle_data:
            vehicle_model.objects.update_or_create(
                plate=plate,
                defaults={
                    'model': model,
                    'year': year,
                    'mileage': 0,
                    'status': 'AVAILABLE',
                    'daily_rate': Decimal('120.00'),
                    'deposit_amount': Decimal('300.00'),
                    'required_license_category': license_category,
                    'minimum_driver_age': minimum_age,
                    'branch': branches[branch_name],
                    **specific_fields,
                },
            )

        customer_data = (
            ('Ana Silva', '11111111111', 'ana@example.test', '11990000001', date(1990, 5, 10), 'LIC0001', 'B'),
            ('Bruno Costa', '22222222222', 'bruno@example.test', '11990000002', date(1987, 8, 21), 'LIC0002', 'AB'),
            ('Carla Souza', '33333333333', 'carla@example.test', '11990000003', date(1995, 2, 14), 'LIC0003', 'A'),
            ('Diego Lima', '44444444444', 'diego@example.test', '11990000004', date(1982, 11, 3), 'LIC0004', 'C'),
        )
        for name, national_id, email, phone, birth_date, license_number, category in customer_data:
            customer, _ = Customer.objects.update_or_create(
                national_id=national_id,
                defaults={
                    'full_name': name,
                    'email': email,
                    'phone': phone,
                    'birth_date': birth_date,
                    'status': Customer.Status.ACTIVE,
                },
            )
            DriverLicense.objects.update_or_create(
                customer=customer,
                defaults={
                    'number': license_number,
                    'category': category,
                    'expires_on': date(2030, 12, 31),
                },
            )

        BasicInsurance.objects.update_or_create(
            name='Básico',
            defaults={
                'daily_cost': Decimal('25.00'),
                'deductible': Decimal('3000.00'),
                'coverage_limit': Decimal('5000.00'),
            },
        )
        FullInsurance.objects.update_or_create(
            name='Completo',
            defaults={
                'daily_cost': Decimal('45.00'),
                'deductible': Decimal('1000.00'),
                'coverage_limit': Decimal('50000.00'),
                'third_party_coverage': True,
                'roadside_assistance': True,
            },
        )

        employee_data = (
            ('Marina Gerente', 'marina@example.test', 'MANAGER', 'Centro'),
            ('Paulo Atendente', 'paulo@example.test', 'ATTENDANT', 'Centro'),
            ('Rita Atendente', 'rita@example.test', 'ATTENDANT', 'Jardins'),
        )
        for name, email, role, branch_name in employee_data:
            Employee.objects.update_or_create(
                email=email,
                defaults={
                    'full_name': name,
                    'role': role,
                    'branch_id': branches[branch_name].pk,
                    'is_active': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Base de demonstração criada/atualizada.'))
