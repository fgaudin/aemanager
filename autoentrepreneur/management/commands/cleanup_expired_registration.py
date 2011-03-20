from django.core.management.base import BaseCommand
from bugtracker.models import Issue, Comment, Vote
from django.conf import settings
import datetime
from registration.models import RegistrationProfile

class Command(BaseCommand):
    help = 'Delete users with expired registration'

    def handle(self, *args, **options):
        """
        Delete inactive users which have an expired registration
        Expired registrations have expiration_key <> from RegistrationProfile.ACTIVATED
        AND user.date_joined <= today - settings.ACCOUNT_ACTIVATION_DAYS

        """
        expired_registrations = RegistrationProfile.objects.filter(user__is_active=False,
                                                                   user__date_joined__lte=datetime.date.today() - datetime.timedelta(settings.ACCOUNT_ACTIVATION_DAYS)).exclude(activation_key=RegistrationProfile.ACTIVATED)

        i = 0
        for registration in expired_registrations:
            i = i + 1
            registration.user.delete()

        print "%i expired subscription(s) deleted" % (i)
