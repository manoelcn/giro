from django.contrib import admin

from customers.models import BasicInsurance, Customer, DriverLicense, FullInsurance, Insurance


admin.site.register((Customer, DriverLicense, Insurance, BasicInsurance, FullInsurance))
