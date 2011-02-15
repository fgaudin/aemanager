from django.test import TestCase
from django.contrib.auth.models import User
from autoentrepreneur.models import Subscription, SUBSCRIPTION_STATE_NOT_PAID, \
    SUBSCRIPTION_STATE_TRIAL, SUBSCRIPTION_STATE_PAID, SUBSCRIPTION_STATE_FREE, \
    UserProfile
from django.db.utils import IntegrityError
from contact.models import Contact, Address, CONTACT_TYPE_COMPANY
from project.models import Project, PROJECT_STATE_PROSPECT, Proposal, \
    PROPOSAL_STATE_DRAFT, ROW_CATEGORY_SERVICE, ProposalRow
from accounts.models import Invoice, INVOICE_STATE_PAID, PAYMENT_TYPE_CHECK, \
    InvoiceRow, Expense
from bugtracker.models import ISSUE_CATEGORY_BUG, ISSUE_STATE_OPEN, Issue, \
    Comment, Vote
from django.core.urlresolvers import reverse
import datetime

class SubcriptionTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        Subscription.objects.all().delete()

    def testNotAllowedIfNoSubscription(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfSubscriptionNotPaid(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfSubscriptionNotPaidWithFutureDate(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfTrialFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfPaidFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testAllowedIfPaidNotFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXY')
        self.assertTrue(profile.is_allowed())

    def testAllowedIfTrialNotFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testAllowedIfFreeAccount(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testAllowedIfFreeAccountWithFinishedDate(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testNextDateBeforeExpiration(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(375))

    def testNextDateAfterExpiration(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() - datetime.timedelta(10),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(365))

    def testNextDateWhenPaymentFails(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(365),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(365))

    def testNextDateWhenPaymentFailsWithRunningSubscription(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(375),
                                    transaction_id='XXY')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(375))

    def testTransactionIdIsUnique(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        s = Subscription(owner=user,
                         state=SUBSCRIPTION_STATE_NOT_PAID,
                         expiration_date=datetime.date.today() + datetime.timedelta(375),
                         transaction_id='XXX')

        self.assertRaises(IntegrityError, s.save)

class UnregisterTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testUnregister(self):
        address = Address.objects.create(street='',
                                         zipcode='',
                                         city='',
                                         country_id=7,
                                         owner_id=1)
        contact = Contact.objects.create(contact_type=CONTACT_TYPE_COMPANY,
                                         name='Contact name',
                                         firstname='',
                                         function='',
                                         company_id='',
                                         legal_form='',
                                         representative='',
                                         representative_function='',
                                         email='',
                                         address=address,
                                         owner_id=1)
        project = Project.objects.create(name='Project test',
                                         customer=contact,
                                         state=PROJECT_STATE_PROSPECT,
                                         owner_id=1)
        proposal = Proposal.objects.create(project=project,
                                           update_date=datetime.date.today(),
                                           state=PROPOSAL_STATE_DRAFT,
                                           begin_date=datetime.date(2010, 8, 1),
                                           end_date=datetime.date(2010, 8, 15),
                                           contract_content='Content of contract',
                                           amount=2005,
                                           owner_id=1)
        proposal_row = ProposalRow.objects.create(proposal=proposal,
                                                  label='Day of work',
                                                  category=ROW_CATEGORY_SERVICE,
                                                  quantity=20,
                                                  unit_price='200.5',
                                                  owner_id=1)
        invoice = Invoice.objects.create(customer=contact,
                                         invoice_id=1,
                                         state=INVOICE_STATE_PAID,
                                         amount='100',
                                         edition_date=datetime.date(2010, 8, 31),
                                         payment_date=datetime.date(2010, 9, 30),
                                         paid_date=None,
                                         payment_type=PAYMENT_TYPE_CHECK,
                                         execution_begin_date=datetime.date(2010, 8, 1),
                                         execution_end_date=datetime.date(2010, 8, 7),
                                         penalty_date=datetime.date(2010, 10, 8),
                                         penalty_rate='1.5',
                                         discount_conditions='Nothing',
                                         owner_id=1)

        invoice_row = InvoiceRow.objects.create(proposal=proposal,
                                                invoice=invoice,
                                                label='Day of work',
                                                category=ROW_CATEGORY_SERVICE,
                                                quantity=10,
                                                unit_price='10',
                                                balance_payments=False,
                                                owner_id=1)
        expense = Expense.objects.create(date=datetime.date(2010, 1, 1),
                                         reference='ABCD',
                                         amount='100.0',
                                         payment_type=PAYMENT_TYPE_CHECK,
                                         description='First expense',
                                         owner_id=1)
        issue = Issue.objects.create(owner_id=1,
                                     category=ISSUE_CATEGORY_BUG,
                                     subject='test',
                                     message='test',
                                     update_date=datetime.datetime.now(),
                                     state=ISSUE_STATE_OPEN)
        comment = Comment.objects.create(owner_id=1,
                                         message='comment',
                                         update_date=datetime.datetime.now(),
                                         issue=issue)
        vote = Vote.objects.create(issue=issue,
                                   owner_id=1)

        response = self.client.get(reverse('unregister'))
        self.assertEquals(response.status_code, 200)

        response = self.client.post(reverse('unregister'),
                                    {'unregister': 'ok'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Address.objects.count(), 2)
        self.assertEquals(Contact.objects.count(), 0)
        self.assertEquals(Project.objects.count(), 0)
        self.assertEquals(Proposal.objects.count(), 0)
        self.assertEquals(ProposalRow.objects.count(), 0)
        self.assertEquals(Invoice.objects.count(), 0)
        self.assertEquals(InvoiceRow.objects.count(), 0)
        self.assertEquals(Expense.objects.count(), 0)
        self.assertEquals(Issue.objects.count(), 1)
        self.assertEquals(Comment.objects.count(), 1)
        self.assertEquals(Vote.objects.count(), 0)
        self.assertEquals(Subscription.objects.filter(owner__id=1).count(), 0)
        self.assertEquals(User.objects.filter(pk=1).count(), 0)
        self.assertEquals(UserProfile.objects.filter(pk=1).count(), 0)
