from decimal import Decimal

from fleet.models import Inspection


class InspectionService:
    def register(
        self,
        rental_id: int,
        inspection_type: str,
        km: int,
        damages: Decimal = Decimal('0.00'),
    ) -> Inspection:
        return Inspection.objects.create(
            rental_id=rental_id,
            inspection_type=inspection_type,
            mileage=km,
            damages=damages,
        )

    def get(self, rental_id: int, inspection_type: str) -> Inspection | None:
        return Inspection.objects.filter(
            rental_id=rental_id,
            inspection_type=inspection_type,
        ).first()
