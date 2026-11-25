from django.db.models import QuerySet

from rentals.models import Rental


class RentalRepository:
    def get(self, rental_id: int) -> Rental | None:
        return (
            Rental.objects.select_related('reservation')
            .filter(pk=rental_id)
            .first()
        )

    def list(self) -> QuerySet[Rental]:
        return Rental.objects.select_related('reservation')
