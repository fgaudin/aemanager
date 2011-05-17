from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from notification.models import Notification
from project.models import Proposal, PROPOSAL_STATE_ACCEPTED
import datetime
from accounts.models import Invoice, INVOICE_STATE_EDITED, INVOICE_STATE_SENT
from django.core.management import call_command
from django.core import mail

class NotificationTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.user = User.objects.get(pk=1)
        self.proposal1 = Proposal.objects.create(project_id=30,
                                                 reference='crt1234',
                                                 update_date=datetime.date.today(),
                                                 state=PROPOSAL_STATE_ACCEPTED,
                                                 begin_date=datetime.date(2010, 8, 1),
                                                 end_date=datetime.date(2010, 8, 15),
                                                 contract_content='Content of contract',
                                                 amount=1000,
                                                 owner_id=1)

        self.proposal2 = Proposal.objects.create(project_id=30,
                                                 reference='crt1234',
                                                 update_date=datetime.date.today(),
                                                 state=PROPOSAL_STATE_ACCEPTED,
                                                 begin_date=datetime.date(2010, 8, 1),
                                                 end_date=datetime.date(2010, 8, 15),
                                                 contract_content='Content of contract',
                                                 amount=1000,
                                                 owner_id=2)

    def test_get_edit(self):
        response = self.client.get(reverse('notification_edit'))
        self.assertEquals(response.status_code, 200)

    def test_post_edit(self):
        notification = self.user.notification
        self.assertTrue(notification.notify_late_invoices)
        self.assertTrue(notification.notify_invoices_to_send)
        self.assertTrue(notification.notify_bug_comments)

        response = self.client.post(reverse('notification_edit'),
                                    {'notify_late_invoices': False,
                                     'notify_invoices_to_send': False,
                                     'notify_bug_comments': False})
        self.assertEquals(response.status_code, 302)
        updated_notification = Notification.objects.get(user=self.user)
        self.assertFalse(updated_notification.notify_late_invoices)
        self.assertFalse(updated_notification.notify_invoices_to_send)
        self.assertFalse(updated_notification.notify_bug_comments)

    def test_no_email_sent_when_notification_set_to_false(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='100',
                                   edition_date=datetime.date.today() - datetime.timedelta(1),
                                   payment_date=datetime.date.today() - datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        notification = self.user.notification
        notification.notify_invoices_to_send = False
        notification.save()

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 0)

    def test_no_email_send_if_no_invoices(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='100',
                                   edition_date=datetime.date.today() + datetime.timedelta(1),
                                   payment_date=datetime.date.today() + datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 0)

    def test_late_invoices(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_SENT,
                                   amount='100',
                                   edition_date=datetime.date.today() - datetime.timedelta(3),
                                   payment_date=datetime.date.today() - datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, u"Vous avez des factures \xe0 traiter")
        self.assertEquals(mail.outbox[0].to, ['%s %s <%s>' % (self.user.first_name, self.user.last_name, self.user.email)])
        self.assertEquals(mail.outbox[0].body, u"Vous avez des factures en attente d'une action de votre part.\n\nLe paiement des factures suivantes est en retard. Soit vous avez re\xe7u le paiement et vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez relancer vos clients :\n\n - Facture 1 \xe0 Contact 1 (date de paiement : 17/05/2011)\n\n\nRendez vous sur votre tableau de bord pour voir et modifier ces factures : https://example.com/\n\nPour modifier vos param\xe8tres de notification : https://example.com/home/notifications/\n\nL'\xe9quipe example.com\n\nVous recevez cet email car vous \xeates inscrit(e) sur https://example.com. Si vous voulez quitter le site, veuillez cliquer sur le lien ci-dessous pour vous d\xe9sinscrire. Attention, si vous avez un abonnement, celui-ci sera perdu.\nhttps://example.com/home/unregister/")

    def test_invoices_to_send(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='100',
                                   edition_date=datetime.date.today() - datetime.timedelta(1),
                                   payment_date=datetime.date.today() + datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, u"Vous avez des factures \xe0 traiter")
        self.assertEquals(mail.outbox[0].to, ['%s %s <%s>' % (self.user.first_name, self.user.last_name, self.user.email)])
        self.assertEquals(mail.outbox[0].body, u'Vous avez des factures en attente d\'une action de votre part.\n\nLa date d\'\xe9dition des factures suivantes est d\xe9pass\xe9e et elles n\'ont toujours pas le statut "envoy\xe9e". Soit vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez les envoyer \xe0 vos clients :\n\n - Facture 1 \xe0 Contact 1 (date d\'\xe9dition : 17/05/2011)\n\nRendez vous sur votre tableau de bord pour voir et modifier ces factures : https://example.com/\n\nPour modifier vos param\xe8tres de notification : https://example.com/home/notifications/\n\nL\'\xe9quipe example.com\n\nVous recevez cet email car vous \xeates inscrit(e) sur https://example.com. Si vous voulez quitter le site, veuillez cliquer sur le lien ci-dessous pour vous d\xe9sinscrire. Attention, si vous avez un abonnement, celui-ci sera perdu.\nhttps://example.com/home/unregister/')

    def test_twice(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='100',
                                   edition_date=datetime.date.today() - datetime.timedelta(1),
                                   payment_date=datetime.date.today() + datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_SENT,
                                    amount='100',
                                    edition_date=datetime.date.today() - datetime.timedelta(3),
                                    payment_date=datetime.date.today() - datetime.timedelta(1),
                                    paid_date=None,
                                    owner_id=1)

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, u"Vous avez des factures \xe0 traiter")
        self.assertEquals(mail.outbox[0].to, ['%s %s <%s>' % (self.user.first_name, self.user.last_name, self.user.email)])
        self.assertEquals(mail.outbox[0].body, u'Vous avez des factures en attente d\'une action de votre part.\n\nLe paiement des factures suivantes est en retard. Soit vous avez re\xe7u le paiement et vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez relancer vos clients :\n\n - Facture 2 \xe0 Contact 1 (date de paiement : 17/05/2011)\n\nLa date d\'\xe9dition des factures suivantes est d\xe9pass\xe9e et elles n\'ont toujours pas le statut "envoy\xe9e". Soit vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez les envoyer \xe0 vos clients :\n\n - Facture 1 \xe0 Contact 1 (date d\'\xe9dition : 17/05/2011)\n\nRendez vous sur votre tableau de bord pour voir et modifier ces factures : https://example.com/\n\nPour modifier vos param\xe8tres de notification : https://example.com/home/notifications/\n\nL\'\xe9quipe example.com\n\nVous recevez cet email car vous \xeates inscrit(e) sur https://example.com. Si vous voulez quitter le site, veuillez cliquer sur le lien ci-dessous pour vous d\xe9sinscrire. Attention, si vous avez un abonnement, celui-ci sera perdu.\nhttps://example.com/home/unregister/')

    def test_one_email_by_user(self):
        i = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_EDITED,
                                   amount='100',
                                   edition_date=datetime.date.today() - datetime.timedelta(1),
                                   payment_date=datetime.date.today() + datetime.timedelta(1),
                                   paid_date=None,
                                   owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal1.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_SENT,
                                    amount='100',
                                    edition_date=datetime.date.today() - datetime.timedelta(3),
                                    payment_date=datetime.date.today() - datetime.timedelta(1),
                                    paid_date=None,
                                    owner_id=2)

        call_command('notify_users')

        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[0].subject, u"Vous avez des factures \xe0 traiter")
        self.assertEquals(mail.outbox[0].to, ['%s %s <%s>' % (self.user.first_name, self.user.last_name, self.user.email)])
        self.assertEquals(mail.outbox[0].body, u'Vous avez des factures en attente d\'une action de votre part.\n\nLa date d\'\xe9dition des factures suivantes est d\xe9pass\xe9e et elles n\'ont toujours pas le statut "envoy\xe9e". Soit vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez les envoyer \xe0 vos clients :\n\n - Facture 1 \xe0 Contact 1 (date d\'\xe9dition : 17/05/2011)\n\nRendez vous sur votre tableau de bord pour voir et modifier ces factures : https://example.com/\n\nPour modifier vos param\xe8tres de notification : https://example.com/home/notifications/\n\nL\'\xe9quipe example.com\n\nVous recevez cet email car vous \xeates inscrit(e) sur https://example.com. Si vous voulez quitter le site, veuillez cliquer sur le lien ci-dessous pour vous d\xe9sinscrire. Attention, si vous avez un abonnement, celui-ci sera perdu.\nhttps://example.com/home/unregister/')
        user2 = User.objects.get(pk=2)
        self.assertEquals(mail.outbox[1].subject, u"Vous avez des factures \xe0 traiter")
        self.assertEquals(mail.outbox[1].to, ['%s %s <%s>' % (user2.first_name, user2.last_name, user2.email)])
        self.assertEquals(mail.outbox[1].body, u"Vous avez des factures en attente d'une action de votre part.\n\nLe paiement des factures suivantes est en retard. Soit vous avez re\xe7u le paiement et vous avez oubli\xe9 de les mettre \xe0 jour, soit vous devriez relancer vos clients :\n\n - Facture 2 \xe0 Contact 1 (date de paiement : 17/05/2011)\n\n\nRendez vous sur votre tableau de bord pour voir et modifier ces factures : https://example.com/\n\nPour modifier vos param\xe8tres de notification : https://example.com/home/notifications/\n\nL'\xe9quipe example.com\n\nVous recevez cet email car vous \xeates inscrit(e) sur https://example.com. Si vous voulez quitter le site, veuillez cliquer sur le lien ci-dessous pour vous d\xe9sinscrire. Attention, si vous avez un abonnement, celui-ci sera perdu.\nhttps://example.com/home/unregister/")
