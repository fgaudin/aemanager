from django.contrib import admin
from contact.models import Contact, PhoneNumber, Address, Country, \
    CompanySearchEngine

admin.site.register(Country)
admin.site.register(Contact)
admin.site.register(PhoneNumber)
admin.site.register(Address)
admin.site.register(CompanySearchEngine)
