from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from fleet.api.serializers import (
    AvailabilityQuerySerializer,
    BranchSerializer,
    InspectionRegisterSerializer,
    InspectionSerializer,
    MaintenanceSerializer,
    MaintenanceStartSerializer,
    VehicleSerializer,
    VehicleWriteSerializer,
)
from fleet.models import Branch, Inspection, Maintenance, Vehicle
from rentals.services.reservation_query import ReservationQuery


class BranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branches = Branch.objects.order_by('name')
        results = BranchSerializer(branches, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})

    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.save()
        return Response(BranchSerializer(branch).data, status=status.HTTP_201_CREATED)


class BranchDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(Branch, pk=pk)

    def get(self, request, pk):
        return Response(BranchSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        branch = self.get_object(pk)
        serializer = BranchSerializer(branch, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        return Response(BranchSerializer(serializer.save()).data)

    def delete(self, request, pk):
        branch = self.get_object(pk)
        try:
            branch.delete()
        except ProtectedError as exc:
            raise ValidationError('Não é possível excluir uma filial com veículos vinculados.') from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


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

    def post(self, request):
        serializer = VehicleWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()
        return Response(
            VehicleSerializer(vehicle).data,
            status=status.HTTP_201_CREATED,
        )


class VehicleDetailView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, pk):
        return get_object_or_404(
            Vehicle.objects.select_related('branch', 'car', 'motorcycle', 'utilityvehicle'),
            pk=pk,
        )

    def get(self, request, pk):
        return Response(VehicleSerializer(self.get_object(pk)).data)

    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        vehicle = self.get_object(pk)
        serializer = VehicleWriteSerializer(vehicle, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        vehicle = serializer.save()
        return Response(VehicleSerializer(vehicle).data)

    def delete(self, request, pk):
        vehicle = self.get_object(pk)
        try:
            vehicle.delete()
        except ProtectedError as exc:
            raise ValidationError('Não é possível excluir um veículo vinculado a registros.') from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class VehicleAvailabilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        serializer = AvailabilityQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        starts_at = serializer.validated_data['starts_at']
        expected_return_at = serializer.validated_data['expected_return_at']
        busy_vehicle_ids = ReservationQuery().busy_vehicle_ids(starts_at, expected_return_at)
        vehicles = Vehicle.objects.filter(status=Vehicle.Status.AVAILABLE).exclude(
            pk__in=busy_vehicle_ids,
        ).select_related('branch', 'car', 'motorcycle', 'utilityvehicle').order_by('model')
        results = VehicleSerializer(vehicles, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})


class InspectionListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        inspections = Inspection.objects.order_by('-created_at')
        rental_id = request.query_params.get('rental_id')
        inspection_type = request.query_params.get('inspection_type')
        if rental_id:
            inspections = inspections.filter(rental_id=rental_id)
        if inspection_type:
            inspections = inspections.filter(inspection_type=inspection_type)
        results = InspectionSerializer(inspections, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})

    def post(self, request):
        serializer = InspectionRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inspection = serializer.save()
        return Response(InspectionSerializer(inspection).data, status=status.HTTP_201_CREATED)


class MaintenanceListCreateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        maintenance_records = Maintenance.objects.select_related('vehicle').order_by('-started_at')
        active = request.query_params.get('active')
        if active == 'true':
            maintenance_records = maintenance_records.filter(completed_at__isnull=True)
        elif active == 'false':
            maintenance_records = maintenance_records.filter(completed_at__isnull=False)
        results = MaintenanceSerializer(maintenance_records, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})

    def post(self, request):
        serializer = MaintenanceStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        maintenance = serializer.save()
        return Response(
            MaintenanceSerializer(maintenance).data,
            status=status.HTTP_201_CREATED,
        )


class MaintenanceReleaseView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        maintenance = get_object_or_404(
            Maintenance.objects.select_related('vehicle'),
            pk=pk,
            completed_at__isnull=True,
        )
        maintenance.vehicle.release()
        maintenance.refresh_from_db()
        return Response(MaintenanceSerializer(maintenance).data)
