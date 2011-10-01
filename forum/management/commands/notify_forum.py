from django.core.management.base import BaseCommand
from accounts.models import Invoice
from django.template import loader
from django.contrib.sites.models import Site
from django.template.context import Context
from django.conf import settings
from django.core.mail import send_mass_mail
from forum.models import MessageNotification
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Send emails to user to notify them about new messages in forum"

    def handle(self, *args, **options):
        notifications = MessageNotification.objects.all()
        # for each notification get all users having forum notification enabled
        # excluding message author
        messages = []

        for notification in notifications:
            topic = notification.message.topic

            notification_email_subject_template = loader.get_template('topic/email_subject.html')
            notification_email_subject_context = {'topic': topic.title}
            subject = notification_email_subject_template.render(Context(notification_email_subject_context))

            notification_email_template = loader.get_template('topic/email.html')
            notification_email_context = {'site': Site.objects.get_current(),
                                          'message': notification.message}
            body = notification_email_template.render(Context(notification_email_context))

            signature_template = loader.get_template('newsletter/signature.html')
            signature_context = {'site': Site.objects.get_current()}
            signature = signature_template.render(Context(signature_context))

            users = User.objects.filter(notification__notify_forum_answers=True,
                                        forum_messages__topic=topic)\
                                .distinct()\
                                .exclude(pk=notification.message.author.id)\
                                .order_by('email')

            for user in users:
                to = '%s %s <%s>' % (user.first_name,
                                     user.last_name,
                                     user.email)

                messages.append((subject,
                                 body + signature,
                                 settings.DEFAULT_FROM_EMAIL,
                                 [to]))

            # delete notification in the loop to prevent deleting new notifications
            # if it were after send_mass_mail
            notification.delete()

        send_mass_mail(messages, fail_silently=False)
        self.stdout.write("%d forum notifications sent.\n" % (len(messages)))
