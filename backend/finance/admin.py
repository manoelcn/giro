from django.contrib import admin

from finance.models import Fine, Payment


admin.site.register((Payment, Fine))
