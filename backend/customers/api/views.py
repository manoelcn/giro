from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.api.serializers import CustomerSerializer, InsuranceSerializer
from customers.models import Customer, Insurance


class CustomerListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        customers = Customer.objects.order_by('full_name')
        results = CustomerSerializer(customers, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})


class InsuranceListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        insurances = Insurance.objects.select_related(
            'basicinsurance',
            'fullinsurance',
        ).order_by('name')
        results = InsuranceSerializer(insurances, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})
