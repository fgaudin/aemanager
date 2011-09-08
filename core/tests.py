from django.utils.translation import ugettext
from project.models import  Proposal, PROPOSAL_STATE_DRAFT, \
    PROPOSAL_STATE_ACCEPTED, ROW_CATEGORY_SERVICE
import datetimestub
import autoentrepreneur
import accounts
import core.views
from autoentrepreneur.models import AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL, \
    Subscription, SUBSCRIPTION_STATE_PAID, SUBSCRIPTION_STATE_FREE, UserProfile
import datetime
from registration.models import RegistrationProfile
from django.test import TestCase
from core.models import OwnedObject
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from accounts.models import Invoice, INVOICE_STATE_EDITED, \
    PAYMENT_TYPE_CHECK, INVOICE_STATE_PAID, InvoiceRow, INVOICE_STATE_SENT

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

class ChangePasswordTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test_user', 'test@example.com', 'test')
        self.client.login(username='test_user', password='test')

    def test_get_page(self):
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)

    def test_fields_mandatory(self):
        response = self.client.post(reverse('change_password'),
                                    {'current_password': '',
                                     'new_password': '',
                                     'retyped_new_password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('current_password' in response.context['passwordform'].errors)
        self.assertTrue('new_password' in response.context['passwordform'].errors)
        self.assertTrue('retyped_new_password' in response.context['passwordform'].errors)

    def test_wrong_current_password(self):
        response = self.client.post(reverse('change_password'),
                                    {'current_password': 'test2',
                                     'new_password': 'test3',
                                     'retyped_new_password': 'test3'})
        self.assertContains(response, ugettext("Wrong password"), status_code=200)

    def test_password_doesnt_match(self):
        response = self.client.post(reverse('change_password'),
                                    {'current_password': 'test',
                                     'new_password': 'test1',
                                     'retyped_new_password': 'test2'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('retyped_new_password' in response.context['passwordform'].errors)

    def test_password_changed(self):
        response = self.client.post(reverse('change_password'),
                                    {'current_password': 'test',
                                     'new_password': 'test2',
                                     'retyped_new_password': 'test2'})
        self.assertContains(response, ugettext("Your password has been modified successfully"), status_code=200)
        self.client.logout()
        logged_in = self.client.login(username='test_user', password='test2')
        self.assertTrue(logged_in)

class DashboardTest(TestCase):
    fixtures = ['test_dashboard']

    def setUp(self):
        self.client.login(username='test', password='test')
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        accounts.models.datetime = datetimestub.DatetimeStub()
        core.views.datetime = datetimestub.DatetimeStub()

    def tearDown(self):
        autoentrepreneur.models.datetime = datetime
        accounts.models.datetime = datetime
        core.views.datetime = datetime

    def testGetDashBoard(self):
        """
        Tests getting dashboard
        """
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def testGetDashBoardWithNewUser(self):
        """
        Tests getting dashboard with a new user
        In order to test default values
        """
        self.client.logout()
        user = User.objects.create_user('new_user', 'test@example.com', 'test')
        self.client.login(username='new_user', password='test')
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('settings_edit'), 302, 200)

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

    def testYearChange(self):
        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1
        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['sales']['paid'], 0)
        self.assertEquals(response.context['sales']['waiting'], 1500)
        self.assertEquals(response.context['sales']['to_be_invoiced'], 750)
        self.assertEquals(response.context['sales']['limit'], 32600)
        self.assertEquals(response.context['sales_previous_year']['paid'], 5000)
        self.assertEquals(response.context['sales_previous_year']['remaining'], 16182 - 5000)
        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 25

    def testProspect(self):
        response = self.client.get(reverse('index'))
        self.assertEquals(float(response.context['prospects']['duration']), 30.0)
        self.assertEquals(set(response.context['prospects']['proposals_to_send']), set(Proposal.objects.filter(pk__in=(24, 26))))
        self.assertEquals(float(response.context['prospects']['potential_sales']), 9500.00)
        self.assertEquals(float(response.context['prospects']['average_unit_price']), 9500.0 / 30.0)
        self.assertEquals(float(response.context['prospects']['percentage_of_remaining']), 9500.0 / 8932.0 * 100.0)

    def testBug70(self):
        """
        Invoices without rows makes dashboard crash
        Only on invoice which never had rows
        """
        response = self.client.post(reverse('invoice_add', kwargs={'customer_id': 3}),
                                    {'contact-name': 'My customer',
                                     'address-street': '1 rue de la paix',
                                     'address-zipcode': '75001',
                                     'address-city': 'Paris',
                                     'invoice-invoice_id': 10,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0})

        self.assertEquals(response.status_code, 302)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.status_code, 200)

    def testTax(self):
        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['period_begin'], datetimestub.DatetimeStub.date(2010, 7, 1))
        self.assertEquals(response.context['taxes']['period_end'], datetimestub.DatetimeStub.date(2010, 12, 31))
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 5000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 7250.0)
        self.assertEquals(float(response.context['taxes']['tax_rate']), 18.3)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 915.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1326.75)
        self.assertEquals(response.context['taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 1, 31))

    def testTaxWithProfessionnalFormation(self):
        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 4
        autoentrepreneur.models.datetime.date.mock_day = 1
        invoice = Invoice.objects.get(pk=20)
        invoice.state = INVOICE_STATE_PAID
        invoice.paid_date = datetimestub.DatetimeStub.date(2011, 2, 1)
        invoice.save()
        profile = User.objects.get(pk=1).get_profile()
        profile.professional_category = AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL
        profile.save()
        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['paid_sales_for_period'], 1500)
        self.assertEquals(response.context['taxes']['tax_rate'], 18.3 + 0.2)
        self.assertEquals(response.context['taxes']['amount_to_pay'], 277.5)
        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 25

    def testBug220(self):
        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 4
        autoentrepreneur.models.datetime.date.mock_day = 30

        profile = User.objects.get(pk=1).get_profile()
        profile.creation_help = True
        profile.freeing_tax_payment = True
        profile.creation_date = datetime.date(2010, 4, 16)
        profile.save()

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['tax_rate'], 7.7)
        self.assertEquals(response.context['next_taxes']['tax_rate'], 11.6)

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 25

    def testWithInvoiceWithoutProposal(self):
        response = self.client.post(reverse('invoice_add_without_proposal'),
                                    {'contact-name': 'New customer',
                                     'address-street': '1 rue de la paix',
                                     'address-zipcode': '75001',
                                     'address-city': 'Paris',
                                     'invoice-invoice_id': 10,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 1,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': '',
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 10,
                                     'invoice_rows-0-unit_price': 100 })

        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 5000)
        self.assertEqual(response.context['sales']['waiting'], 1500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 1750)
        self.assertEqual(response.context['sales']['total'], 8250)
        self.assertEqual(response.context['sales']['remaining'], 7932)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 5000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 915.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

        invoice = Invoice.objects.get(invoice_id=10)
        invoice.state = INVOICE_STATE_SENT
        invoice.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 5000)
        self.assertEqual(response.context['sales']['waiting'], 2500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 750)
        self.assertEqual(response.context['sales']['total'], 8250)
        self.assertEqual(response.context['sales']['remaining'], 7932)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 5000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 915.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

        invoice = Invoice.objects.get(invoice_id=10)
        invoice.state = INVOICE_STATE_PAID
        invoice.paid_date = datetime.date(2010, 9, 10)
        invoice.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 6000)
        self.assertEqual(response.context['sales']['waiting'], 1500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 750)
        self.assertEqual(response.context['sales']['total'], 8250)
        self.assertEqual(response.context['sales']['remaining'], 7932)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 6000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 1098.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

    def testWithInvoiceWithAndWithoutProposal(self):
        """
        one row have proposal, the other not
        """
        proposal = Proposal.objects.get(pk=24)
        proposal.state = PROPOSAL_STATE_ACCEPTED
        proposal.save()

        response = self.client.post(reverse('invoice_add_without_proposal'),
                                    {'contact-customer_id': proposal.project.customer.id,
                                     'contact-name': 'New customer',
                                     'address-street': '1 rue de la paix',
                                     'address-zipcode': '75001',
                                     'address-city': 'Paris',
                                     'invoice-invoice_id': 10,
                                     'invoice-state': INVOICE_STATE_EDITED,
                                     'invoice-amount': 1000,
                                     'invoice-edition_date': '2010-8-31',
                                     'invoice-payment_date': '2010-9-30',
                                     'invoice-paid_date': '',
                                     'invoice-payment_type': PAYMENT_TYPE_CHECK,
                                     'invoice-execution_begin_date': '2010-8-1',
                                     'invoice-execution_end_date': '2010-8-7',
                                     'invoice-penalty_date': '2010-10-8',
                                     'invoice-penalty_rate': 1.5,
                                     'invoice-discount_conditions':'Nothing',
                                     'invoice_rows-TOTAL_FORMS': 2,
                                     'invoice_rows-INITIAL_FORMS': 0,
                                     'invoice_rows-0-ownedobject_ptr': '',
                                     'invoice_rows-0-label': 'Day of work',
                                     'invoice_rows-0-proposal': '',
                                     'invoice_rows-0-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-0-quantity': 6,
                                     'invoice_rows-0-unit_price': 100,
                                     'invoice_rows-1-ownedobject_ptr': '',
                                     'invoice_rows-1-label': 'Day of work',
                                     'invoice_rows-1-proposal': 24,
                                     'invoice_rows-1-category': ROW_CATEGORY_SERVICE,
                                     'invoice_rows-1-quantity': 4,
                                     'invoice_rows-1-unit_price': 100 })

        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 5000)
        self.assertEqual(response.context['sales']['waiting'], 1500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 8350)
        self.assertEqual(response.context['sales']['total'], 14850)
        self.assertEqual(response.context['sales']['remaining'], 1332)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 5000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 915.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

        invoice = Invoice.objects.get(invoice_id=10)
        invoice.state = INVOICE_STATE_SENT
        invoice.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 5000)
        self.assertEqual(response.context['sales']['waiting'], 2500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 7350)
        self.assertEqual(response.context['sales']['total'], 14850)
        self.assertEqual(response.context['sales']['remaining'], 1332)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 5000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 915.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

        invoice = Invoice.objects.get(invoice_id=10)
        invoice.state = INVOICE_STATE_PAID
        invoice.paid_date = datetime.date(2010, 9, 10)
        invoice.save()

        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 6000)
        self.assertEqual(response.context['sales']['waiting'], 1500)
        self.assertEqual(response.context['sales']['to_be_invoiced'], 7350)
        self.assertEqual(response.context['sales']['total'], 14850)
        self.assertEqual(response.context['sales']['remaining'], 1332)
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 6000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 8250.0)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 1098.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 1509.75)

class DashboardProductActivityTest(TestCase):
    fixtures = ['test_dashboard_product_sales']

    def setUp(self):
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        accounts.models.datetime = datetimestub.DatetimeStub()
        core.views.datetime = datetimestub.DatetimeStub()
        self.client.login(username='test', password='test')
        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

    def tearDown(self):
        autoentrepreneur.models.datetime = datetime
        accounts.models.datetime = datetime
        core.views.datetime = datetime

    def testServicePaid(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['paid'], 60)
        self.assertEqual(response.context['sales']['service_paid'], 50)

    def testServiceWaiting(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['waiting'], 130)
        self.assertEqual(response.context['sales']['service_waiting'], 80)

    def testServiceToBeInvoiced(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['to_be_invoiced'], 60)
        self.assertEqual(response.context['sales']['service_to_be_invoiced'], 30)

    def testServiceTotal(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['total'], 250)
        self.assertEqual(response.context['sales']['service_total'], 160)

    def testServiceRemaining(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['remaining'], 81250)
        self.assertEqual(response.context['sales']['service_remaining'], 32440)

    def testServiceLimit(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['sales']['limit'], 81500)
        self.assertEqual(response.context['sales']['service_limit'], 32600)

class PreviousTaxTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        datetimestub.DatetimeStub.date.mock_year = 2011
        datetimestub.DatetimeStub.date.mock_month = 5
        datetimestub.DatetimeStub.date.mock_day = 1
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        accounts.models.datetime = datetimestub.DatetimeStub()
        core.views.datetime = datetimestub.DatetimeStub()

        profile = UserProfile.objects.get(user=1)
        profile.creation_help = True
        profile.freeing_tax_payment = True
        profile.creation_date = datetime.date(2010, 4, 15)
        profile.save()
        self.client.login(username='test', password='test')
        self.proposal = Proposal.objects.create(project_id=30,
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_ACCEPTED,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=40000,
                                                owner_id=1)

    def tearDown(self):
        autoentrepreneur.models.datetime = datetime
        accounts.models.datetime = datetime
        core.views.datetime = datetime
        datetimestub.DatetimeStub.date.mock_year = 2010
        datetimestub.DatetimeStub.date.mock_month = 10
        datetimestub.DatetimeStub.date.mock_day = 25

    def testPreviousTax(self):
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='1000',
                                   edition_date=datetime.date(2011, 2, 1),
                                   payment_date=datetime.date(2011, 2, 1),
                                   paid_date=datetime.date(2011, 2, 1),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='100',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_PAID,
                                    amount='2000',
                                    edition_date=datetime.date(2011, 4, 1),
                                    payment_date=datetime.date(2011, 4, 1),
                                    paid_date=datetime.date(2011, 4, 1),
                                    payment_type=PAYMENT_TYPE_CHECK,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)
        i_row2 = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                           invoice_id=i2.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=10,
                                           unit_price='200',
                                           balance_payments=False,
                                           owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 4, 1))
        self.assertEquals(response.context['taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 6, 30))
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 2000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 2000.0)
        self.assertEquals(float(response.context['taxes']['tax_rate']), 11.6)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 232.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 232.0)
        self.assertEquals(response.context['taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 7, 31))

        self.assertEquals(response.context['previous_taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(response.context['previous_taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 3, 31))
        self.assertEquals(float(response.context['previous_taxes']['paid_sales_for_period']), 1000.0)
        self.assertEquals(float(response.context['previous_taxes']['tax_rate']), 7.7)
        self.assertEquals(float(response.context['previous_taxes']['amount_to_pay']), 77.0)
        self.assertEquals(response.context['previous_taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 4, 30))

    def testPreviousTaxOverruning(self):
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32700',
                                   edition_date=datetime.date(2011, 2, 1),
                                   payment_date=datetime.date(2011, 2, 1),
                                   paid_date=datetime.date(2011, 2, 1),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=1,
                                          unit_price='32700',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_PAID,
                                    amount='2000',
                                    edition_date=datetime.date(2011, 4, 1),
                                    payment_date=datetime.date(2011, 4, 1),
                                    paid_date=datetime.date(2011, 4, 1),
                                    payment_type=PAYMENT_TYPE_CHECK,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)
        i_row2 = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                           invoice_id=i2.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=10,
                                           unit_price='200',
                                           balance_payments=False,
                                           owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 4, 1))
        self.assertEquals(response.context['taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 6, 30))
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 2000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 2000.0)
        self.assertEquals(float(response.context['taxes']['tax_rate']), 18.5)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 370.0)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 370.0)
        self.assertEquals(response.context['taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 7, 31))

        self.assertEquals(response.context['previous_taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(response.context['previous_taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 3, 31))
        self.assertEquals(float(response.context['previous_taxes']['paid_sales_for_period']), 32700.0)
        self.assertEquals(float(response.context['previous_taxes']['tax_rate']), 5.5)
        self.assertEquals(float(response.context['previous_taxes']['amount_to_pay']), 1793.0)
        self.assertEquals(float(response.context['previous_taxes']['extra_taxes']), 18.5)
        self.assertEquals(response.context['previous_taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 4, 30))

    def testPreviousTaxWithCurrentOverruning(self):
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='30000',
                                   edition_date=datetime.date(2011, 2, 1),
                                   payment_date=datetime.date(2011, 2, 1),
                                   paid_date=datetime.date(2011, 2, 1),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=1,
                                          unit_price='30000',
                                          balance_payments=False,
                                          owner_id=1)

        i2 = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                    invoice_id=2,
                                    state=INVOICE_STATE_PAID,
                                    amount='3000',
                                    edition_date=datetime.date(2011, 4, 1),
                                    payment_date=datetime.date(2011, 4, 1),
                                    paid_date=datetime.date(2011, 4, 1),
                                    payment_type=PAYMENT_TYPE_CHECK,
                                    execution_begin_date=datetime.date(2010, 8, 1),
                                    execution_end_date=datetime.date(2010, 8, 7),
                                    penalty_date=datetime.date(2010, 10, 8),
                                    penalty_rate='1.5',
                                    discount_conditions='Nothing',
                                    owner_id=1)
        i_row2 = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                           invoice_id=i2.id,
                                           label='Day of work',
                                           category=ROW_CATEGORY_SERVICE,
                                           quantity=10,
                                           unit_price='300',
                                           balance_payments=False,
                                           owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 4, 1))
        self.assertEquals(response.context['taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 6, 30))
        self.assertEquals(float(response.context['taxes']['paid_sales_for_period']), 3000.0)
        self.assertEquals(float(response.context['taxes']['estimated_paid_sales_for_period']), 3000.0)
        self.assertEquals(float(response.context['taxes']['tax_rate']), 9.2 + 0.2)
        self.assertEquals(float(response.context['taxes']['amount_to_pay']), 2600 * (9.2 + 0.2) / 100)
        self.assertEquals(float(response.context['taxes']['estimated_amount_to_pay']), 2600 * (9.2 + 0.2) / 100)
        self.assertEquals(float(response.context['taxes']['extra_taxes']), 74)
        self.assertEquals(response.context['taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 7, 31))

        self.assertEquals(response.context['previous_taxes']['period_begin'], datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(response.context['previous_taxes']['period_end'], datetimestub.DatetimeStub.date(2011, 3, 31))
        self.assertEquals(float(response.context['previous_taxes']['paid_sales_for_period']), 30000.0)
        self.assertEquals(float(response.context['previous_taxes']['tax_rate']), 7.7)
        self.assertEquals(float(response.context['previous_taxes']['amount_to_pay']), 2310.0)
        self.assertEquals(response.context['previous_taxes']['tax_due_date'], datetimestub.DatetimeStub.date(2011, 4, 30))

    def testNoPreviousTaxForFirstPeriod(self):
        profile = UserProfile.objects.get(user=1)
        profile.creation_date = datetime.date(2011, 4, 15)
        profile.save()

        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='30000',
                                   edition_date=datetime.date(2011, 2, 1),
                                   payment_date=datetime.date(2011, 2, 1),
                                   paid_date=datetime.date(2011, 2, 1),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=1,
                                          unit_price='30000',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['previous_taxes'], None)

class OverrunTest(TestCase):
    fixtures = ['test_users', 'test_contacts', 'test_projects']

    def setUp(self):
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        accounts.models.datetime = datetimestub.DatetimeStub()
        core.views.datetime = datetimestub.DatetimeStub()

        self.client.login(username='test', password='test')
        self.proposal = Proposal.objects.create(project_id=30,
                                                update_date=datetime.date.today(),
                                                state=PROPOSAL_STATE_ACCEPTED,
                                                begin_date=datetime.date(2010, 8, 1),
                                                end_date=datetime.date(2010, 8, 15),
                                                contract_content='Content of contract',
                                                amount=1000,
                                                owner_id=1)

    def tearDown(self):
        autoentrepreneur.models.datetime = datetime
        accounts.models.datetime = datetime
        core.views.datetime = datetime
        datetimestub.DatetimeStub.date.mock_year = 2010
        datetimestub.DatetimeStub.date.mock_month = 10
        datetimestub.DatetimeStub.date.mock_day = 25

    def testNoMessageWhenNoOverrun(self):
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, 'leave')

    def testWarningWhenProposalsOverrunFirstLimit(self):
        self.proposal.amount = 32200
        self.proposal.save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attention, you will leave the Auto-entrepreneur status at the end of the next year if all your proposals and invoices are paid before the end of the year.')
        self.assertNotContains(response, 'You have to declare VAT from the first month of overrun.')
        self.assertNotContains(response, 'Attention, you will lose tax rates associated with creation help for overrunning sales if all your proposals and invoices are paid before the end of the year.')
        self.assertNotContains(response, 'Attention, you will lose freeing tax payment if all your proposals and invoices are paid before the end of the year.')

    def testWarningWhenProposalsOverrunSecondLimit(self):
        self.proposal.amount = 34200
        self.proposal.save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attention, you will leave the Auto-entrepreneur status at the end of the current year if all your proposals and invoices are paid before the end of the year.')
        self.assertContains(response, 'You have to declare VAT from the first month of overrun.')
        self.assertNotContains(response, 'Attention, you will lose tax rates associated with creation help for overrunning sales if all your proposals and invoices are paid before the end of the year.')

    def testWarningFreeingTaxPaymentWhenProposalsOverrunFirstLimit(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attention, you will lose freeing tax payment if all your proposals and invoices are paid before the end of the year.')

    def testWarningCreationHelpWhenProposalsOverrunFirstLimit(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attention, you will lose tax rates associated with creation help for overrunning sales if all your proposals and invoices are paid before the end of the year.')

    def testWarningCreationHelpWhenProposalsOverrunSecondLimit(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 34200
        self.proposal.save()
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Attention, you will lose tax rates associated with creation help for overrunning sales if all your proposals and invoices are paid before the end of the year.')

    def testWarningWhenInvoicesOverrunFirstLimit(self):
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'You will leave the Auto-entrepreneur status at the end of the next year.')

    def testWarningCreationHelpWhenInvoicesOverrunFirstLimit(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'You lose tax rates associated with creation help for overrunning sales.')

    def testWarningFreeingTaxPaymentWhenInvoicesOverrunFirstLimit(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'You lose freeing tax payment.')

    def testWarningWhenInvoicesOverrunSecondLimit(self):
        self.proposal.amount = 34200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='34200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3420',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'You will leave the Auto-entrepreneur status at the end of the current year.')
        self.assertContains(response, 'You have to declare VAT from the first month of overrun.')

    def testWarningWhenInvoicesOverrunFirstLimitPreviousYear(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        datetimestub.DatetimeStub.date.mock_year = 2011
        datetimestub.DatetimeStub.date.mock_month = 2
        datetimestub.DatetimeStub.date.mock_day = 10

        response = self.client.get(reverse('index'))
        self.assertContains(response, 'You will leave the Auto-entrepreneur status at the end of the current year.')
        self.assertContains(response, 'You lose tax rates associated with creation help for overrunning sales.')
        self.assertContains(response, 'You lose freeing tax payment.')

    def testTaxAmountOnFirstOverrun(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 8, 31),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['tax_rate'], 5.3)
        self.assertEquals(response.context['taxes']['paid_sales_for_period'], 32200)
        self.assertEquals(response.context['taxes']['amount_to_pay'], 1701.3)
        self.assertEquals(response.context['taxes']['extra_taxes'], 18.3)
        self.assertEquals(response.context['taxes']['total_amount_to_pay'], 1719.6)

    def testTaxAmountOnNextPeriodAfterOverrun(self):
        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 4, 30),
                                   payment_date=datetime.date(2010, 4, 30),
                                   paid_date=datetime.date(2010, 4, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=2,
                                   state=INVOICE_STATE_PAID,
                                   amount='300',
                                   edition_date=datetime.date(2010, 9, 30),
                                   payment_date=datetime.date(2010, 9, 30),
                                   paid_date=datetime.date(2010, 9, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='30',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['tax_rate'], 18.3)
        self.assertEquals(response.context['taxes']['paid_sales_for_period'], 300)
        self.assertEquals(response.context['taxes']['amount_to_pay'], 54.9)

    def testTaxAmountOnSecondYearAfterOverrun(self):
        datetimestub.DatetimeStub.date.mock_year = 2011
        datetimestub.DatetimeStub.date.mock_month = 2
        datetimestub.DatetimeStub.date.mock_day = 10

        profile = User.objects.get(pk=1).get_profile()
        profile.freeing_tax_payment = True
        profile.creation_help = True
        profile.save()
        self.proposal.amount = 32200
        self.proposal.save()
        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=1,
                                   state=INVOICE_STATE_PAID,
                                   amount='32200',
                                   edition_date=datetime.date(2010, 4, 30),
                                   payment_date=datetime.date(2010, 4, 30),
                                   paid_date=datetime.date(2010, 4, 30),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='3220',
                                          balance_payments=False,
                                          owner_id=1)

        i = Invoice.objects.create(customer_id=self.proposal.project.customer_id,
                                   invoice_id=2,
                                   state=INVOICE_STATE_PAID,
                                   amount='300',
                                   edition_date=datetime.date(2011, 2, 2),
                                   payment_date=datetime.date(2011, 2, 2),
                                   paid_date=datetime.date(2011, 2, 2),
                                   payment_type=PAYMENT_TYPE_CHECK,
                                   execution_begin_date=datetime.date(2010, 8, 1),
                                   execution_end_date=datetime.date(2010, 8, 7),
                                   penalty_date=datetime.date(2010, 10, 8),
                                   penalty_rate='1.5',
                                   discount_conditions='Nothing',
                                   owner_id=1)
        i_row = InvoiceRow.objects.create(proposal_id=self.proposal.id,
                                          invoice_id=i.id,
                                          label='Day of work',
                                          category=ROW_CATEGORY_SERVICE,
                                          quantity=10,
                                          unit_price='30',
                                          balance_payments=False,
                                          owner_id=1)

        response = self.client.get(reverse('index'))
        self.assertEquals(response.context['taxes']['tax_rate'], 18.5)
        self.assertEquals(response.context['taxes']['paid_sales_for_period'], 300)
        self.assertEquals(response.context['taxes']['amount_to_pay'], 55.5)

class RegisterTest(TestCase):
    def testGetRegisterPage(self):
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)

    def testUserCreation(self):
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'usertest',
                                     'email': 'test@test.com',
                                     'password1': 'test',
                                     'password2':'test',
                                     'tos': 'checked'})
        self.assertEqual(response.status_code, 302)
        users = User.objects.filter(username='usertest')
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].email, 'test@test.com')

    def testEmptyFields(self):
        response = self.client.post(reverse('registration_register'),
                                    {})
        self.assertTrue('username' in response.context['form'].errors)
        self.assertTrue('email' in response.context['form'].errors)
        self.assertTrue('password1' in response.context['form'].errors)
        self.assertTrue('password2' in response.context['form'].errors)

    def testUsernameBadFormated(self):
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'usertest!!',
                                     'email': 'test@test.com',
                                     'password1': 'test',
                                     'password2':'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['username'], ["This value must contain only letters, numbers and underscores."])

    def testUsernameAlreadyExists(self):
        user = User.objects.create_user('test_user', 'test@example.com', 'test')
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'test_user',
                                     'email': 'test@test.com',
                                     'password1': 'test',
                                     'password2':'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['username'], ["A user with that username already exists."])

    def testEmailBadFormated(self):
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'usertest',
                                     'email': 'testtest.com',
                                     'password1': 'test',
                                     'password2':'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['email'], ["Enter a valid e-mail address."])


    def testEmailAlreadyExists(self):
        user = User.objects.create_user('test_user', 'test@example.com', 'test')
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'test_user2',
                                     'email': 'test@example.com',
                                     'password1': 'test',
                                     'password2':'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors['email'], ["This email address is already in use. Please supply a different email address."])

    def testPasswordsDontMatch(self):
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'usertest',
                                     'email': 'test@test.com',
                                     'password1': 'test',
                                     'password2':'test2'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].non_field_errors(), ["The two password fields didn't match."])

class AdminDashboardPermissionTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testPermission(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['title'], 'Log in')

class AdminDashboardTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.user1 = User.objects.get(username='test')
        self.user1.is_superuser = True
        self.user1.is_staff = True
        self.user1.save()
        self.client.login(username='test', password='test')

    def testUsers(self):
        sub1 = Subscription.objects.get(owner=self.user1)
        sub1.state = SUBSCRIPTION_STATE_FREE
        sub1.save()

        user2 = User.objects.get(username='test2')
        sub2 = Subscription.objects.get(owner=user2)
        sub2.expiration_date = datetime.date.today() + datetime.timedelta(10)
        sub2.save()

        user3 = User.objects.create_user('test3', 'test3@example.com', 'test')
        user4 = User.objects.create_user('test4', 'test4@example.com', 'test')
        user5 = User.objects.create_user('test5', 'test5@example.com', 'test')
        user6 = User.objects.create_user('test6', 'test6@example.com', 'test')
        user7 = User.objects.create_user('test7', 'test7@example.com', 'test')
        user8 = User.objects.create_user('test8', 'test8@example.com', 'test')
        user9 = User.objects.create_user('test9', 'test9@example.com', 'test')
        user10 = User.objects.create_user('test10', 'test10@example.com', 'test')
        user11 = User.objects.create_user('test11', 'test11@example.com', 'test')

        user3.is_active = False
        user3.save()
        registration = RegistrationProfile()
        registration.user = user3
        registration.activation_key = '1234'
        registration.save()

        user4.is_active = False
        user4.save()
        profile = user4.get_profile()
        profile.unregister_datetime = datetime.datetime.now()
        profile.save()

        user5.is_active = False
        user5.save()
        profile = user5.get_profile()
        profile.unregister_datetime = datetime.datetime.now()
        profile.save()

        sub6 = Subscription.objects.get(owner=user6)
        sub6.expiration_date = datetime.date.today() - datetime.timedelta(1)
        sub6.save()
        sub7 = Subscription.objects.get(owner=user7)
        sub7.expiration_date = datetime.date.today() - datetime.timedelta(1)
        sub7.save()
        sub8 = Subscription.objects.get(owner=user8)
        sub8.expiration_date = datetime.date.today() - datetime.timedelta(1)
        sub8.save()

        sub9 = Subscription()
        sub9.owner = user9
        sub9.state = SUBSCRIPTION_STATE_PAID
        sub9.expiration_date = datetime.date.today() + datetime.timedelta(1)
        sub9.save()

        response = self.client.get(reverse('admin_dashboard'))
        self.assertEquals(response.status_code, 200)

        users = response.context['users']
        self.assertEquals(users[0]['value'], 10) # total users
        self.assertEquals(users[1]['value'], 1) # unconfirmed users
        self.assertEquals(users[2]['value'], 2) # waiting for deletion
        self.assertEquals(users[3]['value'], 3) # expired users
        self.assertEquals(users[4]['value'], 4) # active users
        self.assertEquals(users[5]['value'], 1) # subscribed users
