from autoentrepreneur.models import AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY, \
    AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY, \
    AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC, \
    AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC, AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC, \
    AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
from django.utils.translation import ugettext
from project.models import  Proposal
import datetimestub
import autoentrepreneur
import accounts
accounts.models.datetime = datetimestub.DatetimeStub()
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
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        self.client.login(username='test', password='test')

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
        self.assertRedirects(response, '/home?next=/', 302, 301)

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

    def testProspect(self):
        response = self.client.get(reverse('index'))
        self.assertEquals(float(response.context['prospects']['duration']), 30.0)
        self.assertEquals(set(response.context['prospects']['proposals_to_send']), set(Proposal.objects.filter(pk__in=(24, 26))))
        self.assertEquals(float(response.context['prospects']['potential_sales']), 9500.00)
        self.assertEquals(float(response.context['prospects']['average_unit_price']), 9500.0 / 30.0)
        self.assertEquals(float(response.context['prospects']['percentage_of_remaining']), 9500.0 / 8932.0 * 100.0)

class DashboardProductActivityTest(TestCase):
    fixtures = ['test_dashboard_product_sales']

    def setUp(self):
        autoentrepreneur.models.datetime = datetimestub.DatetimeStub()
        self.client.login(username='test', password='test')
        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

    def tearDown(self):
        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 25

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

class TaxTest(TestCase):

    def setUp(self):
        user = User.objects.create_user('test_user', 'test@example.com', 'test')
        self.user = authenticate(username='test_user', password='test')

    def testGetQuarter(self):
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 1, 1)), (1, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 2, 1)), (1, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 3, 1)), (1, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 4, 1)), (2, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 5, 1)), (2, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 6, 1)), (2, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 7, 1)), (3, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 8, 1)), (3, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 9, 1)), (3, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 10, 1)), (4, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 11, 1)), (4, 2011))
        self.assertEquals(self.user.get_profile().get_quarter(datetimestub.DatetimeStub.date(2011, 12, 1)), (4, 2011))

    def testPeriodQuaterlyFirstPayment(self):
        """
        Periodicite trimestrielle
        La premiere declaration trimestrielle porte sur la periode comprise
        entre le debut d'activite et la fin du trimestre civil qui suit.
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts5
        """
        profile = self.user.get_profile()
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2011, 1, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 6, 30))

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 12, 31)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 12, 31))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 3, 31))

        # first case of www.lautoentrepreneur.fr
        profile.creation_date = datetimestub.DatetimeStub.date(2010, 2, 1)
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 3
        autoentrepreneur.models.datetime.date.mock_day = 1
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 5
        autoentrepreneur.models.datetime.date.mock_day = 31
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 6
        autoentrepreneur.models.datetime.date.mock_day = 30
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 7
        autoentrepreneur.models.datetime.date.mock_day = 1
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))


        # second case of www.lautoentrepreneur.fr
        profile.creation_date = datetimestub.DatetimeStub.date(2010, 7, 10)
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 7
        autoentrepreneur.models.datetime.date.mock_day = 10

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 12, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 8
        autoentrepreneur.models.datetime.date.mock_day = 10

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 12, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 12
        autoentrepreneur.models.datetime.date.mock_day = 31

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 12, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 12, 31))

    def testPeriodQuaterlySecondPayment(self):
        profile = self.user.get_profile()
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 8
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 1, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 9, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 1, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 9, 30))


        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 7, 10)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 3, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 4
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 7, 10)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 3, 31))

    def testPeriodMonthlyFirstPayment(self):
        """
        Periodicite mensuelle
        La premiere declaration mensuelle porte sur la periode comprise entre
        le debut d'activite et la fin du troisieme mois civil qui suit.
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts5
        """
        profile = self.user.get_profile()
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2011, 1, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2011, 1, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 4, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 12, 31)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 12, 31))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 3, 31))

        # first case of www.lautoentrepreneur.fr
        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 2, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 5, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 3
        autoentrepreneur.models.datetime.date.mock_day = 1

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 5, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 5
        autoentrepreneur.models.datetime.date.mock_day = 31

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 5, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 6
        autoentrepreneur.models.datetime.date.mock_day = 1

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 2, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 5, 31))

        # second case of www.lautoentrepreneur.fr
        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 7
        autoentrepreneur.models.datetime.date.mock_day = 10

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 7, 10)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 10, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 8
        autoentrepreneur.models.datetime.date.mock_day = 1

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 10, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 10
        autoentrepreneur.models.datetime.date.mock_day = 31

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 10, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 11
        autoentrepreneur.models.datetime.date.mock_day = 1

        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 7, 10))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 10, 31))

    def testPeriodMonthlySecondPayment(self):
        profile = self.user.get_profile()
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_MONTHLY
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 6
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2011, 1, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2011, 5, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2011, 5, 31))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 7
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 2, 1)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 6, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 6, 30))

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 12
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.creation_date = datetimestub.DatetimeStub.date(2010, 7, 10)
        profile.save()
        begin_date, end_date = profile.get_period_for_tax()
        self.assertEquals(begin_date, datetimestub.DatetimeStub.date(2010, 11, 1))
        self.assertEquals(end_date, datetimestub.DatetimeStub.date(2010, 11, 30))

    def testBaseRate(self):
        """
        Without creation help and without freeing tax payment
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts1
        """
        profile = self.user.get_profile()
        profile.creation_date = datetimestub.DatetimeStub.date(2011, 1, 1)
        profile.freeing_tax_payment = False
        profile.creation_help = False
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 21.3)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 21.3)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 18.3)

    def testRateWithFreeingTaxPayment(self):
        """
        Without creation help and with freeing tax payment
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts1
        """
        profile = self.user.get_profile()
        profile.creation_date = datetimestub.DatetimeStub.date(2011, 1, 1)
        profile.freeing_tax_payment = True
        profile.creation_help = False
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2011
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 13.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 23.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 23.5)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 20.5)

    def testRateWithCreationHelpWithoutFreeingTaxPayment(self):
        """
        With creation help and without freeing tax payment
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts1
        """
        profile = self.user.get_profile()
        profile.creation_date = datetimestub.DatetimeStub.date(2007, 1, 1)
        profile.freeing_tax_payment = False
        profile.creation_help = True
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2007
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 3.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.3)

        autoentrepreneur.models.datetime.date.mock_year = 2008
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 3.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 5.3)

        autoentrepreneur.models.datetime.date.mock_year = 2008
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 6.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 9.2)

        autoentrepreneur.models.datetime.date.mock_year = 2009
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 6.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 9.2)

        autoentrepreneur.models.datetime.date.mock_year = 2009
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 9.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 13.8)

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 9.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 13.8)

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 21.3)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 21.3)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 18.3)

    def testRateWithCreationHelpWithFreeingTaxPayment(self):
        """
        With creation help and freeing tax payment
        http://www.lautoentrepreneur.fr/questions_reponses.htm#Couts1
        """
        profile = self.user.get_profile()
        profile.creation_date = datetimestub.DatetimeStub.date(2007, 1, 1)
        profile.freeing_tax_payment = True
        profile.creation_help = True
        profile.save()

        autoentrepreneur.models.datetime.date.mock_year = 2007
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 4.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.1)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.6)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.5)

        autoentrepreneur.models.datetime.date.mock_year = 2008
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 4.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.1)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.6)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.5)

        autoentrepreneur.models.datetime.date.mock_year = 2008
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.9)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 11.4)

        autoentrepreneur.models.datetime.date.mock_year = 2009
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 7.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.4)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 12.9)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 11.4)

        autoentrepreneur.models.datetime.date.mock_year = 2009
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 17.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 18.2)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 1
        autoentrepreneur.models.datetime.date.mock_day = 31

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 10.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 17.7)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 18.2)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 16.0)

        autoentrepreneur.models.datetime.date.mock_year = 2010
        autoentrepreneur.models.datetime.date.mock_month = 2
        autoentrepreneur.models.datetime.date.mock_day = 1

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_PRODUCT_SALE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 13.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BIC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 23.0)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_SERVICE_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 23.5)

        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.save()
        self.assertEquals(profile.get_tax_rate(), 20.5)

class RegisterTest(TestCase):
    def testGetRegisterPage(self):
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)

    def testUserCreation(self):
        response = self.client.post(reverse('registration_register'),
                                    {'username': 'usertest',
                                     'email': 'test@test.com',
                                     'password1': 'test',
                                     'password2':'test'})
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
