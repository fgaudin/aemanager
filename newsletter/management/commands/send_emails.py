from django.core.management.base import BaseCommand, CommandError
from newsletter.models import Message, USER_TYPE_SUBSCRIPTION_PAID, \
    USER_TYPE_SUBSCRIPTION_TRIAL, USER_TYPE_SUBSCRIPTION_EXPIRED
from autoentrepreneur.models import Subscription
from django.conf import settings
from django.core.mail import send_mass_mail
from django.template import loader
from django.contrib.sites.models import Site
from django.template.context import Context

class Command(BaseCommand):
    help = 'Send newsletter emails (not already sent)'

    def handle(self, *args, **options):
        signature_template = loader.get_template('newsletter/signature.html')
        signature_context = {'site': Site.objects.get_current()}
        signature = signature_template.render(Context(signature_context))

        for message in Message.objects.filter(sent=False):
            message.sent = True
            message.save()
            recipients = []
            if message.to == USER_TYPE_SUBSCRIPTION_PAID:
                recipients = Subscription.objects.get_users_with_paid_subscription()
            elif message.to == USER_TYPE_SUBSCRIPTION_TRIAL:
                recipients = Subscription.objects.get_users_with_trial_subscription()
            elif message.to == USER_TYPE_SUBSCRIPTION_EXPIRED:
                recipients = Subscription.objects.get_users_with_expired_subscription()

            messages = []
            for recipient in recipients:
                to = '%s %s <%s>' % (recipient['owner__first_name'],
                                     recipient['owner__last_name'],
                                     recipient['owner__email'])
                messages.append((message.subject,
                                 message.message + signature,
                                 settings.DEFAULT_FROM_EMAIL,
                                 [to]))
            print "Sending \"%s\" to %s ..." % (message.subject, message.get_to_display())
            send_mass_mail(messages, fail_silently=False)
            print "Done"
        else:
            print "Nothing to send"
