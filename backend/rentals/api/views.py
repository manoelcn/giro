from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rentals.api.serializers import (
    PickupSerializer,
    ReservationCreateSerializer,
    ReservationInputSerializer,
    ReservationListFilterSerializer,
    ReservationSerializer,
    RentalListFilterSerializer,
    RentalSerializer,
    ReturnSerializer,
)
from rentals.models import Reservation
from rentals.services.factories import get_rental_service, get_reservation_service
from rentals.services.rental_query import RentalQuery


def get_rental_query() -> RentalQuery:
    return RentalQuery()


class ReservationQuoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReservationInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        quote = get_reservation_service().quote(**serializer.validated_data)
        return Response(
            {
                'daily_rate': format(quote.daily_rate, '.2f'),
                'first_day_amount': format(quote.first_day_amount, '.2f'),
                'quoted_total': format(quote.quoted_total, '.2f'),
                'currency': 'BRL',
            }
        )


class ReservationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters_serializer = ReservationListFilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        reservations = get_reservation_service().repository.list(
            **filters_serializer.validated_data
        )
        results = ReservationSerializer(reservations, many=True).data
        return Response({'count': len(results), 'next': None, 'results': results})

    def post(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation, _ = get_reservation_service().create(**serializer.validated_data)
        return Response(ReservationSerializer(reservation).data, status=201)


class ReservationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reservation_id: int):
        reservation = get_object_or_404(
            Reservation.objects.select_related('rental'),
            pk=reservation_id,
        )
        return Response(ReservationSerializer(reservation).data)


class ReservationCancellationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reservation_id: int):
        quote = get_reservation_service().cancellation_quote(reservation_id)
        charge = (
            {
                'type': 'CANCELLATION',
                'amount': format(quote.cancellation_charge, '.2f'),
                'status': 'PENDING',
            }
            if quote.cancellation_charge is not None
            else None
        )
        return Response({'cancellation_charge': charge})

    def post(self, request, reservation_id: int):
        result = get_reservation_service().cancel(reservation_id)
        charge = (
            {
                'type': 'CANCELLATION',
                'amount': format(result.cancellation_charge.amount, '.2f'),
                'status': result.cancellation_charge.status,
            }
            if result.cancellation_charge is not None
            else None
        )
        return Response(
            {
                'id': result.reservation.pk,
                'status': result.reservation.status,
                'cancellation_charge': charge,
            }
        )


class RentalPickupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rental_id: int):
        serializer = PickupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rental = get_rental_service().pick_up(
            rental_id,
            inspection_id=serializer.validated_data['inspection_id'],
        )
        return Response(
            {
                'id': rental.pk,
                'status': rental.status,
                'picked_up_at': rental.picked_up_at,
            }
        )


class RentalReturnView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rental_id: int):
        serializer = ReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = get_rental_service().return_vehicle(
            rental_id,
            inspection_id=serializer.validated_data['inspection_id'],
            return_branch_id=serializer.validated_data['return_branch_id'],
        )
        return Response(
            {
                'id': result.rental.pk,
                'status': result.rental.status,
                'returned_at': result.rental.returned_at,
                'late_day_count': result.late_day_count,
                'late_charge_amount': format(result.late_charge_amount, '.2f'),
                'inter_branch_charge_amount': format(
                    result.inter_branch_charge_amount,
                    '.2f',
                ),
                'damage_charge_amount': format(result.damage_charge_amount, '.2f'),
                'balance_due': format(result.balance_due, '.2f'),
            }
        )


class RentalFinalizeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, rental_id: int):
        rental = get_rental_service().finalize(rental_id)
        return Response(
            {
                'id': rental.pk,
                'status': rental.status,
                'finalized_at': rental.finalized_at,
            }
        )


class RentalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        filters_serializer = RentalListFilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        rentals = get_rental_query().list(**filters_serializer.validated_data)
        results = RentalSerializer(rentals, many=True).data
        alerts = get_rental_service().overdue_alerts()
        return Response(
            {
                'count': len(results),
                'next': None,
                'results': results,
                'overdue_alerts': [
                    {
                        'rental_id': alert.rental_id,
                        'affected_reservation_id': alert.affected_reservation_id,
                        'equivalent_vehicle_ids': alert.equivalent_vehicle_ids,
                    }
                    for alert in alerts
                ],
            }
        )
