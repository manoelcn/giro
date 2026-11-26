from django.urls import path

from fleet.api.views import (
    BranchDetailView,
    BranchListView,
    InspectionListCreateView,
    MaintenanceListCreateView,
    MaintenanceReleaseView,
    VehicleAvailabilityView,
    VehicleDetailView,
    VehicleListView,
)

app_name = 'fleet'

urlpatterns = [
    path('branches', BranchListView.as_view(), name='branch-list'),
    path('branches/<int:pk>', BranchDetailView.as_view(), name='branch-detail'),
    path('vehicles', VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>', VehicleDetailView.as_view(), name='vehicle-detail'),
    path('availability', VehicleAvailabilityView.as_view(), name='vehicle-availability'),
    path('inspections', InspectionListCreateView.as_view(), name='inspection-list-create'),
    path('maintenance', MaintenanceListCreateView.as_view(), name='maintenance-list-create'),
    path(
        'maintenance/<int:pk>/release',
        MaintenanceReleaseView.as_view(),
        name='maintenance-release',
    ),
]
