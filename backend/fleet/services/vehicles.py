from dataclasses import dataclass
from decimal import Decimal

from fleet.models import Vehicle


@dataclass(frozen=True)
class RentalTerms:
    daily_rate: Decimal
    minimum_deposit: Decimal
    required_license_category: str
    minimum_age: int
    status: str


class VehicleService:
    DAILY_RATE = Decimal('120.00')
    DEPOSIT_AMOUNT = Decimal('300.00')

    def get_rental_terms(self, vehicle_id: int) -> RentalTerms:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
        return RentalTerms(
            daily_rate=self.DAILY_RATE,
            minimum_deposit=self.DEPOSIT_AMOUNT,
            required_license_category=vehicle.required_license_category,
            minimum_age=vehicle.minimum_driver_age,
            status=vehicle.status,
        )

    def mark_reserved(self, vehicle_id: int) -> None:
        self._set_status(vehicle_id, Vehicle.Status.RESERVED)

    def mark_rented(self, vehicle_id: int) -> None:
        self._set_status(vehicle_id, Vehicle.Status.RENTED)

    def release(self, vehicle_id: int) -> None:
        self._set_status(vehicle_id, Vehicle.Status.AVAILABLE)

    @staticmethod
    def _set_status(vehicle_id: int, status: str) -> None:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
        vehicle.status = status
        vehicle.save(update_fields=('status',))
