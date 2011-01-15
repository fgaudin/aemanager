from project.models import PROPOSAL_STATE_BALANCED
import datetimestub
import autoentrepreneur
autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
from django.test import TestCase
from core.models import OwnedObject
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from accounts.models import Invoice

class PermissionTest(TestCase):
    def test_save_owned_object(self):
        """
        Tests that saving an object set user passed in param
        owner except for superusers, where it preserves
        current owner if exists
        """
        user = User.objects.create_user('test_user', 'test@example.com', 'test')
        user = authenticate(username='test_user', password='test')
        ownedObject = OwnedObject()
        ownedObject.save(user=user)
        self.assertEqual(ownedObject.owner, user)

        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        admin = authenticate(username='admin', password='admin')
        ownedObject.save(user=admin)
        self.assertEqual(ownedObject.owner, user)

        ownedObject2 = OwnedObject()
        ownedObject2.save(user=admin)
        self.assertEqual(ownedObject2.owner, admin)

class DashboardTest(TestCase):
    fixtures = ['test_dashboard']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testGetDashBoard(self):
        """
        Tests getting dashboard
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    # test on sales widget
    def testPaidSales(self):
        """
        Tests computation of paid sales
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 5000)

    def testWaitingPayments(self):
        """
        Tests computation of waiting payments
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['waiting'], 1500)

    def testToBeInvoiced(self):
        """
        Tests computation of to be invoiced
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['to_be_invoiced'], 750)

    def testTotal(self):
        """
        Tests computation of total sales
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['total'], 7250)

    def testRemaining(self):
        """
        Tests computation of remaining sales to do
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['remaining'], 8932)

    def testOverrun(self):
        """
        Tests computation of overrun
        """
        i = Invoice.objects.get(invoice_id=4)
        row = i.invoice_rows.all()[0]
        p = row.proposal
        p.amount = p.amount + 8933
        p.save()
        i.amount = i.amount + 8933
        i.save()
        row.quantity = 1
        row.unit_price = i.amount
        row.save()
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['remaining'], -1)

    def testLimit(self):
        """
        Tests computation of sales limit
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['limit'], 16182)

    # test on invoices widget
    def testLateInvoices(self):
        """
        Tests computation of late invoices
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(set(response.context['invoices']['late']), set([Invoice.objects.get(invoice_id=4)]))

    def testInvoicesToSend(self):
        """
        Tests computation of invoices to send
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(set(response.context['invoices']['to_send']), set([Invoice.objects.get(invoice_id=5)]))
