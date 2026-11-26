from fleet.models import RentalTerms, Vehicle


class VehicleService:
    def get_rental_terms(self, vehicle_id: int) -> RentalTerms:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
        return vehicle.get_rental_terms()

    def mark_reserved(self, vehicle_id: int) -> None:
        Vehicle.objects.get(pk=vehicle_id).mark_reserved()

    def mark_rented(self, vehicle_id: int) -> None:
        Vehicle.objects.get(pk=vehicle_id).mark_rented()

    def release(self, vehicle_id: int) -> None:
        Vehicle.objects.get(pk=vehicle_id).release()
