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
from django.core import mail
from django.contrib.sites.models import Site
from django.utils.translation import ugettext
from django.conf import settings
from django.core.management import call_command
import datetime

class SubscriptionTest(TestCase):
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
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        expiration_date = datetime.date.today() + datetime.timedelta(10)
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=expiration_date,
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        try:
            computed_next_date = datetime.date(expiration_date.year + 1, expiration_date.month, expiration_date.day)
        except:
            # case of February 29th
            computed_next_date = datetime.date(expiration_date.year + 1, 3, 1)
        self.assertEquals(next_date, computed_next_date)

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
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        expiration_date = datetime.date.today() + datetime.timedelta(10)
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=expiration_date,
                                    transaction_id='XXX')

        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(375),
                                    transaction_id='XXY')

        next_date = profile.get_next_expiration_date()

        try:
            computed_next_date = datetime.date(expiration_date.year + 1, expiration_date.month, expiration_date.day)
        except:
            # case of February 29th
            computed_next_date = datetime.date(expiration_date.year + 1, 3, 1)
        self.assertEquals(next_date, computed_next_date)

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

    def testBug62(self):
        """
        When several subscriptions are valid, is_allowed returns false
        """
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        Subscription.objects.create(owner=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(375),
                                    transaction_id='XXY')

        self.assertTrue(profile.is_allowed())

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

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, ugettext("You've just unregistered from %(site)s") % {'site': Site.objects.get_current()})
        self.assertEquals(mail.outbox[0].to, ['test@example.com'])
        self.assertFalse(User.objects.get(pk=1).is_active)
        self.assertTrue(UserProfile.objects.get(pk=1).unregister_datetime is not None)

        call_command('delete_unregistered_users')

        self.assertEquals(User.objects.filter(pk=1).count(), 1)
        self.assertEquals(UserProfile.objects.filter(pk=1).count(), 1)

        profile = UserProfile.objects.get(pk=1)
        profile.unregister_datetime = profile.unregister_datetime - datetime.timedelta(settings.ACCOUNT_UNREGISTER_DAYS)
        profile.save()

        call_command('delete_unregistered_users')

        self.assertEquals(Address.objects.count(), 1)
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

class SubscriptionUserSelect(TestCase):

    def setUp(self):
        # user in trial period
        self.user1 = User.objects.create_user('user1', 'user1@example.com', 'test')
        self.user1.first_name = 'User 1'
        self.user1.last_name = 'User 1'
        self.user1.save()
        # user in trial but having paid to continue
        self.user2 = User.objects.create_user('user2', 'user2@example.com', 'test')
        self.user2.first_name = 'User 2'
        self.user2.last_name = 'User 2'
        self.user2.save()
        Subscription.objects.create(owner=self.user2,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='paiduser2')
        # user after trial with paid subscription
        self.user3 = User.objects.create_user('user3', 'user3@example.com', 'test')
        self.user3.first_name = 'User 3'
        self.user3.last_name = 'User 3'
        self.user3.save()
        sub = Subscription.objects.get(owner=self.user3)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(10)
        sub.save()
        Subscription.objects.create(owner=self.user3,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='paiduser3')
        # user with expired trial subscription
        self.user4 = User.objects.create_user('user4', 'user4@example.com', 'test')
        self.user4.first_name = 'User 4'
        self.user4.last_name = 'User 4'
        self.user4.save()
        sub = Subscription.objects.get(owner=self.user4)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(10)
        sub.save()
        # user with expired paid subscription
        self.user5 = User.objects.create_user('user5', 'user5@example.com', 'test')
        self.user5.first_name = 'User 5'
        self.user5.last_name = 'User 5'
        self.user5.save()
        sub = Subscription.objects.get(owner=self.user5)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(20)
        sub.save()
        Subscription.objects.create(owner=self.user5,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(10),
                                    transaction_id='paiduser5')
        # user with free pass during trial
        self.user6 = User.objects.create_user('user6', 'user6@example.com', 'test')
        self.user6.first_name = 'User 6'
        self.user6.last_name = 'User 6'
        self.user6.save()
        Subscription.objects.create(owner=self.user6,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='freeuser6')
        # user with free pass after trial
        self.user7 = User.objects.create_user('user7', 'user7@example.com', 'test')
        self.user7.first_name = 'User 7'
        self.user7.last_name = 'User 7'
        self.user7.save()
        sub = Subscription.objects.get(owner=self.user7)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(20)
        sub.save()
        Subscription.objects.create(owner=self.user7,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='freeuser7')
        # unregistered user in trial
        self.user8 = User.objects.create_user('user8', 'user8@example.com', 'test')
        self.user8.first_name = 'User 8'
        self.user8.last_name = 'User 8'
        self.user8.is_active = False
        self.user8.save()
        profile = self.user8.get_profile()
        profile.unregister_datetime = datetime.datetime.now()
        profile.save()
        # unregistered user with paid subscription
        self.user9 = User.objects.create_user('user9', 'user9@example.com', 'test')
        self.user9.first_name = 'User 9'
        self.user9.last_name = 'User 9'
        self.user9.is_active = False
        self.user9.save()
        profile = self.user9.get_profile()
        profile.unregister_datetime = datetime.datetime.now()
        profile.save()
        sub = Subscription.objects.get(owner=self.user9)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(10)
        sub.save()
        Subscription.objects.create(owner=self.user9,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='paiduser9')
        # unregistered user with expired subscription
        self.user10 = User.objects.create_user('user10', 'user10@example.com', 'test')
        self.user10.first_name = 'User 10'
        self.user10.last_name = 'User 10'
        self.user10.is_active = False
        self.user10.save()
        profile = self.user10.get_profile()
        profile.unregister_datetime = datetime.datetime.now()
        profile.save()
        sub = Subscription.objects.get(owner=self.user10)
        sub.expiration_date = datetime.date.today() - datetime.timedelta(10)
        sub.save()

    def testTrialUser(self):
        users = Subscription.objects.get_users_with_trial_subscription()
        intented_user = {'owner__email':u'user1@example.com',
                          'owner__first_name':u'User 1',
                          'owner__last_name':u'User 1'}
        self.assertEquals(users[0], intented_user)

    def testPaidUser(self):
        users = Subscription.objects.get_users_with_paid_subscription()
        intented_user1 = {'owner__email':u'user2@example.com',
                          'owner__first_name':u'User 2',
                          'owner__last_name':u'User 2'}
        intented_user2 = {'owner__email':u'user3@example.com',
                          'owner__first_name':u'User 3',
                          'owner__last_name':u'User 3'}
        self.assertEquals(len(users), 2)
        self.assertTrue(intented_user1 in users)
        self.assertTrue(intented_user2 in users)

    def testExpiredUser(self):
        users = Subscription.objects.get_users_with_expired_subscription()
        intented_user1 = {'owner__email':u'user4@example.com',
                          'owner__first_name':u'User 4',
                          'owner__last_name':u'User 4'}
        intented_user2 = {'owner__email':u'user5@example.com',
                          'owner__first_name':u'User 5',
                          'owner__last_name':u'User 5'}
        self.assertEquals(len(users), 2)
        self.assertTrue(intented_user1 in users)
        self.assertTrue(intented_user2 in users)
