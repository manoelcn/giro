from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from fleet.models import (
    Branch,
    Car,
    Inspection,
    Maintenance,
    Motorcycle,
    UtilityVehicle,
    Vehicle,
)
from rentals.models import Rental


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('id', 'name', 'address', 'city', 'state')


class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    doors = serializers.SerializerMethodField()
    trunk_capacity_liters = serializers.SerializerMethodField()
    displacement_cc = serializers.SerializerMethodField()
    helmet_included = serializers.SerializerMethodField()
    load_capacity_kg = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = (
            'id',
            'plate',
            'model',
            'year',
            'mileage',
            'status',
            'daily_rate',
            'deposit_amount',
            'required_license_category',
            'minimum_driver_age',
            'branch',
            'branch_name',
            'vehicle_type',
            'last_maintenance_mileage',
            'maintenance_interval_km',
            'doors',
            'trunk_capacity_liters',
            'displacement_cc',
            'helmet_included',
            'load_capacity_kg',
        )

    @staticmethod
    def _subtype_value(obj, relation, field):
        subtype = getattr(obj, relation, None)
        return getattr(subtype, field, None) if subtype is not None else None

    def get_doors(self, obj):
        return self._subtype_value(obj, 'car', 'doors')

    def get_trunk_capacity_liters(self, obj):
        return self._subtype_value(obj, 'car', 'trunk_capacity_liters')

    def get_displacement_cc(self, obj):
        return self._subtype_value(obj, 'motorcycle', 'displacement_cc')

    def get_helmet_included(self, obj):
        return self._subtype_value(obj, 'motorcycle', 'helmet_included')

    def get_load_capacity_kg(self, obj):
        return self._subtype_value(obj, 'utilityvehicle', 'load_capacity_kg')


class VehicleWriteSerializer(serializers.ModelSerializer):
    vehicle_type = serializers.ChoiceField(
        choices=('VEHICLE', 'CAR', 'MOTORCYCLE', 'UTILITYVEHICLE'),
        required=False,
    )
    doors = serializers.IntegerField(required=False, min_value=1)
    trunk_capacity_liters = serializers.IntegerField(required=False, min_value=0)
    displacement_cc = serializers.IntegerField(required=False, min_value=1)
    helmet_included = serializers.BooleanField(required=False)
    load_capacity_kg = serializers.IntegerField(required=False, min_value=1)

    subtype_fields = {
        'CAR': {'doors', 'trunk_capacity_liters'},
        'MOTORCYCLE': {'displacement_cc', 'helmet_included'},
        'UTILITYVEHICLE': {'load_capacity_kg'},
    }

    class Meta:
        model = Vehicle
        fields = (
            'id',
            'plate',
            'model',
            'year',
            'mileage',
            'status',
            'daily_rate',
            'deposit_amount',
            'required_license_category',
            'minimum_driver_age',
            'branch',
            'vehicle_type',
            'maintenance_interval_km',
            'doors',
            'trunk_capacity_liters',
            'displacement_cc',
            'helmet_included',
            'load_capacity_kg',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        current_type = self.instance.vehicle_type if self.instance else None
        vehicle_type = attrs.get('vehicle_type', current_type)
        if vehicle_type is None:
            raise serializers.ValidationError({'vehicle_type': 'Informe o tipo do veículo.'})
        if current_type and vehicle_type != current_type:
            raise serializers.ValidationError(
                {'vehicle_type': 'O tipo do veículo não pode ser alterado.'}
            )

        allowed_fields = self.subtype_fields.get(vehicle_type, set())
        subtype_field_names = set().union(*self.subtype_fields.values())
        supplied_fields = set(attrs) & subtype_field_names
        invalid_fields = supplied_fields - allowed_fields
        if invalid_fields:
            raise serializers.ValidationError(
                {field: 'Campo incompatível com o tipo do veículo.' for field in invalid_fields}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        vehicle_type = validated_data.pop('vehicle_type')
        subtype_data = {
            field: validated_data.pop(field)
            for fields in self.subtype_fields.values()
            for field in fields
            if field in validated_data
        }
        vehicle_class = {
            'VEHICLE': Vehicle,
            'CAR': Car,
            'MOTORCYCLE': Motorcycle,
            'UTILITYVEHICLE': UtilityVehicle,
        }[vehicle_type]
        return vehicle_class.objects.create(**validated_data, **subtype_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('vehicle_type', None)
        subtype_data = {
            field: validated_data.pop(field)
            for fields in self.subtype_fields.values()
            for field in fields
            if field in validated_data
        }
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if subtype_data:
            subtype = getattr(instance, instance.vehicle_type.lower())
            for field, value in subtype_data.items():
                setattr(subtype, field, value)
            subtype.save()
        return instance


class InspectionSerializer(serializers.ModelSerializer):
    has_damage = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inspection
        fields = (
            'id',
            'rental_id',
            'inspection_type',
            'mileage',
            'damages',
            'damage_description',
            'has_damage',
            'created_at',
        )
        read_only_fields = ('id', 'created_at', 'has_damage')


class InspectionRegisterSerializer(serializers.Serializer):
    rental_id = serializers.IntegerField(min_value=1)
    inspection_type = serializers.ChoiceField(choices=Inspection.InspectionType.choices)
    mileage = serializers.IntegerField(min_value=0)
    damages = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.00'),
        default=Decimal('0.00'),
    )
    damage_description = serializers.CharField(max_length=500, allow_blank=True, required=False)

    def validate_rental_id(self, value):
        if not Rental.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Locação não encontrada.')
        if Inspection.objects.filter(
            rental_id=value,
            inspection_type=self.initial_data.get('inspection_type'),
        ).exists():
            raise serializers.ValidationError('Já existe vistoria deste tipo para a locação.')
        return value

    def create(self, validated_data):
        return Inspection.register(
            rental_id=validated_data['rental_id'],
            inspection_type=validated_data['inspection_type'],
            km=validated_data['mileage'],
            damages=validated_data['damages'],
            damage_description=validated_data.get('damage_description', ''),
        )


class AvailabilityQuerySerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField()
    expected_return_at = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs['expected_return_at'] <= attrs['starts_at']:
            raise serializers.ValidationError(
                {'expected_return_at': 'A devolução deve ocorrer depois da retirada.'}
            )
        return attrs


class MaintenanceSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate', read_only=True)
    vehicle_model = serializers.CharField(source='vehicle.model', read_only=True)

    class Meta:
        model = Maintenance
        fields = (
            'id',
            'vehicle',
            'vehicle_plate',
            'vehicle_model',
            'reason',
            'mileage',
            'started_at',
            'completed_at',
        )
        read_only_fields = ('id', 'started_at', 'completed_at')


class MaintenanceStartSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=255)
    mileage = serializers.IntegerField(min_value=0, required=False)

    def validate_vehicle_id(self, value):
        if not Vehicle.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Veículo não encontrado.')
        return value

    def create(self, validated_data):
        vehicle = Vehicle.objects.get(pk=validated_data['vehicle_id'])
        return vehicle.send_to_maintenance(
            reason=validated_data['reason'],
            mileage=validated_data.get('mileage'),
        )
