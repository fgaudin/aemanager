from django.contrib import admin
from accounts.models import Invoice, InvoiceRow, Expense

admin.site.register(Expense)
admin.site.register(Invoice)
admin.site.register(InvoiceRow)
