from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from fleet.api.serializers import BranchSerializer, VehicleSerializer
from fleet.models import Branch, Vehicle


class BranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branches = Branch.objects.order_by('name')
        results = BranchSerializer(branches, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})


class VehicleListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        vehicles = Vehicle.objects.select_related(
            'branch',
            'car',
            'motorcycle',
            'utilityvehicle',
        ).order_by('model')
        results = VehicleSerializer(vehicles, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})
