from django.core.management.base import BaseCommand
from bugtracker.models import Issue, Comment, Vote
from django.conf import settings
from autoentrepreneur.models import UserProfile
import datetime

class Command(BaseCommand):
    help = 'Delete unregistered users'

    def handle(self, *args, **options):
        unregistered_profiles = UserProfile.objects.filter(user__is_active=False,
                                                           unregister_datetime__lt=datetime.datetime.now() - datetime.timedelta(settings.ACCOUNT_UNREGISTER_DAYS))

        i = 0
        for profile in unregistered_profiles:
            i = i + 1
            Issue.objects.filter(owner=profile.user).update(owner=None)
            Comment.objects.filter(owner=profile.user).update(owner=None)
            Vote.objects.filter(owner=profile.user).delete()
            profile.user.delete()

        print "%i user(s) deleted" % (i)
