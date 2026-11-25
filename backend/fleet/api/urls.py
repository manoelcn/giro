from django.urls import path

from fleet.api.views import BranchListView, VehicleListView

app_name = 'fleet'

urlpatterns = [
    path('branches', BranchListView.as_view(), name='branch-list'),
    path('vehicles', VehicleListView.as_view(), name='vehicle-list'),
]
