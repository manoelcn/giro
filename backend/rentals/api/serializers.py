from rest_framework import serializers

from rentals.domain.enums import RentalStatus, ReservationStatus
from rentals.models import Rental, Reservation


class ReservationInputSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1)
    vehicle_id = serializers.IntegerField(min_value=1)
    starts_at = serializers.DateTimeField()
    expected_return_at = serializers.DateTimeField()
    pickup_branch_id = serializers.IntegerField(min_value=1)
    return_branch_id = serializers.IntegerField(min_value=1)
    insurance_id = serializers.IntegerField(
        min_value=1,
        allow_null=True,
        required=False,
        default=None,
    )


class ReservationCreateSerializer(ReservationInputSerializer):
    accepted_total = serializers.DecimalField(max_digits=12, decimal_places=2)


class PickupSerializer(serializers.Serializer):
    inspection_id = serializers.IntegerField(min_value=1)


class ReturnSerializer(serializers.Serializer):
    inspection_id = serializers.IntegerField(min_value=1)
    return_branch_id = serializers.IntegerField(min_value=1)


class ReservationListFilterSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1, required=False)
    vehicle_id = serializers.IntegerField(min_value=1, required=False)
    status = serializers.ChoiceField(
        choices=[status.value for status in ReservationStatus],
        required=False,
    )
    pickup_branch_id = serializers.IntegerField(min_value=1, required=False)
    starts_at = serializers.DateTimeField(required=False)
    expected_return_at = serializers.DateTimeField(required=False)


class RentalListFilterSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(min_value=1, required=False)
    status = serializers.ChoiceField(
        choices=[status.value for status in RentalStatus],
        required=False,
    )
    pickup_branch_id = serializers.IntegerField(min_value=1, required=False)
    starts_at = serializers.DateTimeField(required=False)
    expected_return_at = serializers.DateTimeField(required=False)


class ReservationSerializer(serializers.ModelSerializer):
    rental_id = serializers.SerializerMethodField()
    rental_status = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id',
            'customer_id',
            'vehicle_id',
            'pickup_branch_id',
            'return_branch_id',
            'insurance_id',
            'starts_at',
            'expected_return_at',
            'status',
            'daily_rate_snapshot',
            'quoted_total',
            'first_day_amount_snapshot',
            'created_at',
            'canceled_at',
            'rental_id',
            'rental_status',
        )
        read_only_fields = fields

    def get_rental_id(self, obj: Reservation) -> int | None:
        return obj.rental.pk if hasattr(obj, 'rental') else None

    def get_rental_status(self, obj: Reservation) -> str | None:
        return obj.rental.status if hasattr(obj, 'rental') else None


class RentalSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(source='reservation.customer_id', read_only=True)
    vehicle_id = serializers.IntegerField(source='reservation.vehicle_id', read_only=True)
    pickup_branch_id = serializers.IntegerField(
        source='reservation.pickup_branch_id',
        read_only=True,
    )
    return_branch_id = serializers.IntegerField(
        source='reservation.return_branch_id',
        read_only=True,
    )
    starts_at = serializers.DateTimeField(source='reservation.starts_at', read_only=True)
    expected_return_at = serializers.DateTimeField(
        source='reservation.expected_return_at',
        read_only=True,
    )

    class Meta:
        model = Rental
        fields = (
            'id',
            'customer_id',
            'vehicle_id',
            'status',
            'pickup_branch_id',
            'return_branch_id',
            'actual_return_branch_id',
            'starts_at',
            'expected_return_at',
            'picked_up_at',
            'returned_at',
            'late_day_count',
            'late_charge_amount',
            'inter_branch_charge_amount',
            'damage_charge_amount',
            'finalized_at',
        )
        read_only_fields = fields
