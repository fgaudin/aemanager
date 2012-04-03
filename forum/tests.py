from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from forum.models import Topic, MessageNotification, Message
from autoentrepreneur.models import Subscription, \
    AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC, \
    AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL, \
    AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
import datetime
from django.core.management import call_command
from django.core import mail

class ForumTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')
        self.user = User.objects.get(pk=1)
        self.user2 = User.objects.get(pk=2)

    def testTopicCreate(self):
        response = self.client.get(reverse('topic_create'))
        self.assertEquals(response.status_code, 200)

        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic',
                                     'message-body': 'New message body'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Topic.objects.count(), 1)

        topic = Topic.objects.all()[0]
        self.assertEquals(topic.title, 'New topic')
        self.assertEquals(topic.views, 0)
        self.assertEquals(topic.messages.count(), 1)

        message = topic.messages.all()[0]
        self.assertEquals(message.author, self.user)
        self.assertEquals(message.body, 'New message body')

        self.assertEquals(MessageNotification.objects.count(), 0)

    def testTopicList(self):
        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic',
                                     'message-body': 'New message body'})
        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic 2',
                                     'message-body': 'New message body 2'})

        response = self.client.get(reverse('topic_list'))
        self.assertEquals(response.status_code, 200)
        topics = response.context['topics']
        self.assertEquals(topics.object_list.count(), 2)

    def testTopicDetail(self):
        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic',
                                     'message-body': 'New message body'})

        topic = Topic.objects.all()[0]
        self.assertEquals(topic.views, 0)

        response = self.client.get(reverse('topic_detail', kwargs={'id': topic.id}))
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'New topic')
        self.assertContains(response, 'New message body')
        topic = Topic.objects.get(pk=topic.id)
        self.assertEquals(topic.views, 1)

    def testMessageCreate(self):
        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic',
                                     'message-body': 'New message body'})

        topic = Topic.objects.all()[0]

        response = self.client.post(reverse('topic_detail', kwargs={'id': topic.id}),
                                    {'message-body': 'New answer'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(topic.messages.count(), 2)
        self.assertEquals(topic.messages.all()[1].body, 'New answer')
        self.assertEquals(topic.messages.all()[1].author, self.user)

        response = self.client.get(reverse('topic_detail', kwargs={'id': topic.id}))
        self.assertContains(response, 'New answer')

    def testNotify(self):
        user3 = User.objects.create_user('test3', 'user3@example.com', 'test')
        user3.first_name = 'User 3'
        user3.last_name = 'User 3'
        user3.save()
        profile = user3.get_profile()
        address = profile.address
        address.street = 'test'
        address.zipcode = '75000'
        address.city = 'Paris'
        address.save()
        profile.company_id = '1234'
        profile.activity = AUTOENTREPRENEUR_ACTIVITY_LIBERAL_BNC
        profile.professional_category = AUTOENTREPRENEUR_PROFESSIONAL_CATEGORY_LIBERAL
        profile.creation_date = datetime.date.today()
        profile.payment_option = AUTOENTREPRENEUR_PAYMENT_OPTION_QUATERLY
        profile.save()

        response = self.client.post(reverse('topic_create'),
                                    {'topic-title': 'New topic',
                                     'message-body': 'New message body'})

        self.assertEquals(MessageNotification.objects.count(), 0)

        self.client.logout()
        self.client.login(username='test2', password='test')

        topic = Topic.objects.all()[0]
        response = self.client.post(reverse('topic_detail', kwargs={'id': topic.id}),
                                    {'message-body': 'New answer'})

        self.assertEquals(MessageNotification.objects.count(), 1)
        self.assertEquals(MessageNotification.objects.all()[0].message.body, 'New answer')

        self.client.logout()
        self.client.login(username='test3', password='test')

        response = self.client.post(reverse('topic_detail', kwargs={'id': topic.id}),
                                    {'message-body': 'New answer 2'})

        self.assertEquals(MessageNotification.objects.count(), 1)
        self.assertEquals(MessageNotification.objects.all()[0].message.body, 'New answer 2')

        call_command('notify_forum')

        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(mail.outbox[0].subject, u'Un nouveau message a \xe9t\xe9 post\xe9 en r\xe9ponse \xe0 "New topic"')
        self.assertTrue(mail.outbox[0].body.startswith(u'test3 a r\xe9pondu :\n\nNew answer 2\n\nPour r\xe9pondre \xe0 ce message : https://example.com/forum/topic/detail/2/?page=-1#last'))

        self.assertEquals(mail.outbox[1].to, ['%s %s <%s>' % (self.user.first_name, self.user.last_name, self.user.email)])
        self.assertEquals(mail.outbox[0].to, ['%s %s <%s>' % (self.user2.first_name, self.user2.last_name, self.user2.email)])

        self.assertEquals(MessageNotification.objects.count(), 0)
