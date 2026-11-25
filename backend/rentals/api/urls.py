from django.urls import path

from rentals.api.views import (
    RentalFinalizeView,
    RentalListView,
    RentalPickupView,
    RentalReturnView,
    ReservationCancellationView,
    ReservationDetailView,
    ReservationListCreateView,
    ReservationQuoteView,
)

app_name = 'rentals'

urlpatterns = [
    path('reservations/quote', ReservationQuoteView.as_view(), name='reservation-quote'),
    path('rentals', RentalListView.as_view(), name='rental-list'),
    path(
        'reservations/<int:reservation_id>/cancel',
        ReservationCancellationView.as_view(),
        name='reservation-cancel',
    ),
    path('reservations', ReservationListCreateView.as_view(), name='reservation-list-create'),
    path('rentals/<int:rental_id>/pick-up', RentalPickupView.as_view(), name='rental-pick-up'),
    path('rentals/<int:rental_id>/return', RentalReturnView.as_view(), name='rental-return'),
    path('rentals/<int:rental_id>/finalize', RentalFinalizeView.as_view(), name='rental-finalize'),
    path(
        'reservations/<int:reservation_id>',
        ReservationDetailView.as_view(),
        name='reservation-detail',
    ),
]
