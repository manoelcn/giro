from django.contrib import admin

from fleet.models import Branch, Car, Inspection, Motorcycle, UtilityVehicle, Vehicle


admin.site.register((Branch, Vehicle, Car, Motorcycle, UtilityVehicle, Inspection))
