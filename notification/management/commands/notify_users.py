from django.core.management.base import BaseCommand
from accounts.models import Invoice
from django.template import loader
from django.contrib.sites.models import Site
from django.template.context import Context
from django.conf import settings
from django.core.mail import send_mass_mail

class Command(BaseCommand):
    help = "Send emails to user to notify them regarding their settings"

    def handle(self, *args, **options):
        users = {}
        late_invoices = Invoice.objects.get_late_invoices_for_notification()
        for invoice in late_invoices:
            if invoice.owner.id not in users:
                users[invoice.owner.id] = {'user': invoice.owner}
            if 'late_invoices' not in users[invoice.owner.id]:
                users[invoice.owner.id]['late_invoices'] = []

            users[invoice.owner.id]['late_invoices'].append(invoice)

        invoices_to_send = Invoice.objects.get_invoices_to_send_for_notification()
        for invoice in invoices_to_send:
            if invoice.owner.id not in users:
                users[invoice.owner.id] = {'user': invoice.owner}
            if 'invoices_to_send' not in users[invoice.owner.id]:
                users[invoice.owner.id]['invoices_to_send'] = []

            users[invoice.owner.id]['invoices_to_send'].append(invoice)

        messages = []
        signature_template = loader.get_template('newsletter/signature.html')
        signature_context = {'site': Site.objects.get_current()}
        signature = signature_template.render(Context(signature_context))

        for user in users.values():
            notification_email_subject_template = loader.get_template('notification/email_subject.html')
            notification_email_subject_context = {}
            subject = notification_email_subject_template.render(Context(notification_email_subject_context))

            notification_email_template = loader.get_template('notification/email.html')
            notification_email_context = {'site': Site.objects.get_current()}

            if 'late_invoices' in user:
                notification_email_context['late_invoices'] = user['late_invoices']
            if 'invoices_to_send' in user:
                notification_email_context['invoices_to_send'] = user['invoices_to_send']

            body = notification_email_template.render(Context(notification_email_context))

            to = '%s %s <%s>' % (user['user'].first_name,
                                 user['user'].last_name,
                                 user['user'].email)
            messages.append((subject,
                             body + signature,
                             settings.DEFAULT_FROM_EMAIL,
                             [to]))

        send_mass_mail(messages, fail_silently=False)
