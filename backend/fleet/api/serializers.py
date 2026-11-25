from rest_framework import serializers

from fleet.models import Branch, Vehicle


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ('id', 'name', 'address', 'city', 'state')


class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type = serializers.CharField(read_only=True)
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
            'vehicle_type',
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
