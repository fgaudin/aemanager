from django.contrib import admin
from accounts.models import Invoice, InvoiceRow

admin.site.register(Invoice)
admin.site.register(InvoiceRow)
