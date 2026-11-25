from django.urls import path

from customers.api.views import CustomerListView, InsuranceListView

app_name = 'customers'

urlpatterns = [
    path('customers', CustomerListView.as_view(), name='customer-list'),
    path('insurances', InsuranceListView.as_view(), name='insurance-list'),
]
