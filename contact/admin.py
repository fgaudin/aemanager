from django.contrib import admin
from contact.models import Contact, PhoneNumber, Address
admin.site.register(Contact)
admin.site.register(PhoneNumber)
admin.site.register(Address)
