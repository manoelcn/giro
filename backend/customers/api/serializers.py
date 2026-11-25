from rest_framework import serializers

from customers.models import Customer, Insurance


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('id', 'full_name', 'national_id', 'email', 'phone', 'birth_date', 'status')


class InsuranceSerializer(serializers.ModelSerializer):
    insurance_type = serializers.SerializerMethodField()

    class Meta:
        model = Insurance
        fields = (
            'id',
            'name',
            'daily_cost',
            'deductible',
            'coverage_limit',
            'insurance_type',
        )

    @staticmethod
    def get_insurance_type(obj):
        if hasattr(obj, 'basicinsurance'):
            return 'BASIC'
        if hasattr(obj, 'fullinsurance'):
            return 'FULL'
        return 'INSURANCE'
