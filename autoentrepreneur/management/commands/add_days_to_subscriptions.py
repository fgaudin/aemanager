from django.core.management.base import BaseCommand, CommandError
from autoentrepreneur.models import Subscription

class Command(BaseCommand):
    args = '<days>'
    help = 'Add days to all active subscriptions'

    def handle(self, *args, **options):
        try:
            days = int(args[0])
            self.stdout.write("%i subscriptions updated\n" % (Subscription.objects.add_days(days)))
        except IndexError:
            raise CommandError('You need to pass days to add as argument')
        except ValueError:
            raise CommandError('Days must be an integer')
        except:
            raise
