import shutil
from django.core.management.base import BaseCommand
from bugtracker.models import Issue, Comment, Vote
from django.conf import settings
from autoentrepreneur.models import Subscription
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Delete users with expired subscription > settings.ACCOUNT_EXPIRED_DAYS'

    def handle(self, *args, **options):
        expired_users = Subscription.objects.get_users_with_subscription_expired_for(settings.ACCOUNT_EXPIRED_DAYS)

        i = 0
        for user in expired_users:
            i = i + 1
            user = User.objects.get(pk=user)
            shutil.rmtree('%s%s' % (settings.FILE_UPLOAD_DIR,
                                    user.get_profile().uuid),
                                    True)
            Issue.objects.filter(owner=user).update(owner=None)
            Comment.objects.filter(owner=user).update(owner=None)
            Vote.objects.filter(owner=user).delete()
            user.delete()

        print "%i expired user(s) deleted" % (i)
