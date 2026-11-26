from django.contrib import admin

from fleet.models import (
	Branch,
	Car,
	Inspection,
	Maintenance,
	Motorcycle,
	UtilityVehicle,
	Vehicle,
)


admin.site.register((Branch, Vehicle, Car, Motorcycle, UtilityVehicle, Inspection, Maintenance))
