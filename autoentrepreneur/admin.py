from django.contrib import admin
from autoentrepreneur.models import UserProfile, SalesLimit, Subscription

class SubscriptionAdmin(admin.ModelAdmin):
    ordering = ['owner__username']

admin.site.register(UserProfile)
admin.site.register(SalesLimit)
admin.site.register(Subscription, SubscriptionAdmin)
