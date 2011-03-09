from django.core.management.base import BaseCommand
from autoentrepreneur.models import Subscription
from django.conf import settings
from django.core.mail import send_mass_mail
from django.template import loader
from django.contrib.sites.models import Site
from django.template.context import Context

class Command(BaseCommand):
    help = 'Send an email to users whose subscription will expire soon'

    def handle(self, *args, **options):
        messages = []

        trial_expire_email_subject_template = loader.get_template('core/trial_expire_email_subject.html')
        trial_expire_email_subject_context = {'site': Site.objects.get_current()}
        trial_expire_email_template = loader.get_template('core/trial_expire_email.html')
        trial_expire_email_context = {'site': Site.objects.get_current()}

        expire_in = 7
        trial_expire_email_subject_context['days'] = expire_in
        trial_expire_email_subject = trial_expire_email_subject_template.render(Context(trial_expire_email_subject_context))
        trial_expire_email_context['days'] = expire_in
        trial_expire_email = trial_expire_email_template.render(Context(trial_expire_email_context))
        for recipient in Subscription.objects.get_users_with_trial_subscription_expiring_in(expire_in):
            to = '%s %s <%s>' % (recipient['owner__first_name'],
                                 recipient['owner__last_name'],
                                 recipient['owner__email'])
            messages.append((trial_expire_email_subject,
                             trial_expire_email,
                             settings.DEFAULT_FROM_EMAIL,
                             [to]))

        expire_in = 1
        trial_expire_email_subject_context['days'] = expire_in
        trial_expire_email_subject = trial_expire_email_subject_template.render(Context(trial_expire_email_subject_context))
        trial_expire_email_context['days'] = expire_in
        trial_expire_email = trial_expire_email_template.render(Context(trial_expire_email_context))
        for recipient in Subscription.objects.get_users_with_trial_subscription_expiring_in(expire_in):
            to = '%s %s <%s>' % (recipient['owner__first_name'],
                                 recipient['owner__last_name'],
                                 recipient['owner__email'])
            messages.append((trial_expire_email_subject,
                             trial_expire_email,
                             settings.DEFAULT_FROM_EMAIL,
                             [to]))

        subscription_expire_email_subject_template = loader.get_template('core/subscription_expire_email_subject.html')
        subscription_expire_email_subject_context = {'site': Site.objects.get_current()}
        subscription_expire_email_template = loader.get_template('core/subscription_expire_email.html')
        subscription_expire_email_context = {'site': Site.objects.get_current()}

        expire_in = 7
        subscription_expire_email_subject_context['days'] = expire_in
        subscription_expire_email_subject = subscription_expire_email_subject_template.render(Context(subscription_expire_email_subject_context))
        subscription_expire_email_context['days'] = expire_in
        subscription_expire_email = subscription_expire_email_template.render(Context(subscription_expire_email_context))
        for recipient in Subscription.objects.get_users_with_paid_subscription_expiring_in(expire_in):
            to = '%s %s <%s>' % (recipient['owner__first_name'],
                                 recipient['owner__last_name'],
                                 recipient['owner__email'])
            messages.append((subscription_expire_email_subject,
                             subscription_expire_email,
                             settings.DEFAULT_FROM_EMAIL,
                             [to]))

        expire_in = 1
        subscription_expire_email_subject_context['days'] = expire_in
        subscription_expire_email_subject = subscription_expire_email_subject_template.render(Context(subscription_expire_email_subject_context))
        subscription_expire_email_context['days'] = expire_in
        subscription_expire_email = subscription_expire_email_template.render(Context(subscription_expire_email_context))
        for recipient in Subscription.objects.get_users_with_paid_subscription_expiring_in(expire_in):
            to = '%s %s <%s>' % (recipient['owner__first_name'],
                                 recipient['owner__last_name'],
                                 recipient['owner__email'])
            messages.append((subscription_expire_email_subject,
                             subscription_expire_email,
                             settings.DEFAULT_FROM_EMAIL,
                             [to]))

        if messages:
            print "Sending alert mail to %d users" % (len(messages))
            send_mass_mail(messages, fail_silently=False)
        else:
            print "No users with expiring subscription"
