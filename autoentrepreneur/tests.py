from django.test import TestCase
from django.contrib.auth.models import User
from autoentrepreneur.models import Subscription, SUBSCRIPTION_STATE_NOT_PAID, \
    SUBSCRIPTION_STATE_TRIAL, SUBSCRIPTION_STATE_PAID, SUBSCRIPTION_STATE_FREE
from django.db.utils import IntegrityError
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
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfSubscriptionNotPaidWithFutureDate(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfTrialFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testNotAllowedIfPaidFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertFalse(profile.is_allowed())

    def testAllowedIfPaidNotFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXY')
        self.assertTrue(profile.is_allowed())

    def testAllowedIfTrialNotFinished(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testAllowedIfFreeAccount(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() + datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testAllowedIfFreeAccountWithFinishedDate(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_FREE,
                                    expiration_date=datetime.date.today() - datetime.timedelta(1),
                                    transaction_id='XXX')

        self.assertTrue(profile.is_allowed())

    def testNextDateBeforeExpiration(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(375))

    def testNextDateAfterExpiration(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() - datetime.timedelta(10),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(365))

    def testNextDateWhenPaymentFails(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(365),
                                    transaction_id='XXX')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(365))

    def testNextDateWhenPaymentFailsWithRunningSubscription(self):
        # do not run this test on February 29
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_NOT_PAID,
                                    expiration_date=datetime.date.today() + datetime.timedelta(375),
                                    transaction_id='XXY')

        next_date = profile.get_next_expiration_date()
        self.assertEquals(next_date, datetime.date.today() + datetime.timedelta(375))

    def testTransactionIdIsUnique(self):
        user = User.objects.get(pk=1)
        profile = user.get_profile()
        Subscription.objects.create(user=user,
                                    state=SUBSCRIPTION_STATE_TRIAL,
                                    expiration_date=datetime.date.today() + datetime.timedelta(10),
                                    transaction_id='XXX')

        s = Subscription(user=user,
                         state=SUBSCRIPTION_STATE_NOT_PAID,
                         expiration_date=datetime.date.today() + datetime.timedelta(375),
                         transaction_id='XXX')

        self.assertRaises(IntegrityError, s.save)
