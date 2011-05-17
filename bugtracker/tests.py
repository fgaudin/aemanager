from django.test import TestCase
from bugtracker.models import ISSUE_CATEGORY_BUG, ISSUE_STATE_OPEN, Issue, \
    ISSUE_CATEGORY_FEATURE, ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_STATE_CLOSED, \
    Vote, Comment, ISSUE_CATEGORY_MESSAGE
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.utils.translation import ugettext
from django.contrib.sites.models import Site
import datetime

class IssuePermissionTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testGetEditIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('issue_edit', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostEditIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.post(reverse('issue_edit', kwargs={'id': i1.id}),
                                    {'category': ISSUE_CATEGORY_FEATURE,
                                     'subject': 'test subject2',
                                     'message': 'test message2'})
        self.assertEquals(response.status_code, 404)

    def testGetDeleteIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.get(reverse('issue_delete', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostDeleteIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('issue_delete', kwargs={'id': i1.id}),
                                   {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

    def testGetCloseIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.get(reverse('issue_close', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostCloseIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('issue_close', kwargs={'id': i1.id}),
                                    {'message': 'Closed'})
        self.assertEquals(response.status_code, 404)

    def testPostCloseIssueByAdmin(self):
        user = User.objects.get(pk=1)
        user.is_superuser = True
        user.save()
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('issue_close', kwargs={'id': i1.id}),
                                    {'message': 'Closed'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Issue.objects.get(pk=i1.id).state, ISSUE_STATE_CLOSED)

    def testGetReopenIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)
        response = self.client.get(reverse('issue_reopen', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostReopenIssue(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.post(reverse('issue_reopen', kwargs={'id': i1.id}),
                                    {'message': 'Reopen'})
        self.assertEquals(response.status_code, 404)

    def testPostReopenIssueByAdmin(self):
        user = User.objects.get(pk=1)
        user.is_superuser = True
        user.save()
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.post(reverse('issue_reopen', kwargs={'id': i1.id}),
                                    {'message': 'Reopen'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Issue.objects.get(pk=i1.id).state, ISSUE_STATE_OPEN)

    def testCommentIssue(self):
        """
        Nothing to test
        """
        pass

    def testGetEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.get(reverse('comment_edit', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_edit', kwargs={'id': c1.id}),
                                    {'message': 'comment 2'})
        self.assertEquals(response.status_code, 404)

    def testGetDeleteComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.get(reverse('comment_delete', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostDeleteComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_delete', kwargs={'id': c1.id}),
                                    {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

class MessagePermissionTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testMessageList(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        i2 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('message_list'))
        self.assertEquals(set(response.context['issues']), set([i1]))

    def testIssueDetail(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.get(reverse('issue_detail', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testGetEditMessage(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('issue_edit', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

        i1.owner_id = 2
        i1.save()
        response = self.client.get(reverse('issue_edit', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostEditMessage(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.post(reverse('issue_edit', kwargs={'id': i1.id}),
                                    {'category': ISSUE_CATEGORY_FEATURE,
                                     'subject': 'test subject2',
                                     'message': 'test message2'})
        self.assertEquals(response.status_code, 404)

        i1.owner_id = 2
        i1.save()
        response = self.client.post(reverse('issue_edit', kwargs={'id': i1.id}),
                                    {'category': ISSUE_CATEGORY_FEATURE,
                                     'subject': 'test subject2',
                                     'message': 'test message2'})
        self.assertEquals(response.status_code, 404)

    def testPostDeleteMessage(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('issue_delete', kwargs={'id': i1.id}),
                                   {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

        i1.owner_id = 2
        i1.save()

        response = self.client.post(reverse('issue_delete', kwargs={'id': i1.id}),
                                   {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

    def testCommentMessage(self):
        i1 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})
        self.assertEquals(response.status_code, 404)

        i1.owner_id = 2
        i1.save()

        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})
        self.assertEquals(response.status_code, 404)

    def testGetEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.get(reverse('comment_edit', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 404)

        c1.owner_id = 2
        c1.save()

        response = self.client.get(reverse('comment_edit', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 404)

    def testPostEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_edit', kwargs={'id': c1.id}),
                                    {'message': 'comment 2'})
        self.assertEquals(response.status_code, 404)

        c1.owner_id = 2
        c1.save()

        response = self.client.post(reverse('comment_edit', kwargs={'id': c1.id}),
                                    {'message': 'comment 2'})
        self.assertEquals(response.status_code, 404)

    def testPostDeleteComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_delete', kwargs={'id': c1.id}),
                                    {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

        c1.owner_id = 2
        c1.save()

        response = self.client.post(reverse('comment_delete', kwargs={'id': c1.id}),
                                    {'delete': 'Ok'})
        self.assertEquals(response.status_code, 404)

class IssueTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testIssueList(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        i2 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_FEATURE,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        i3 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_SUBSCRIPTION,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        i4 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.get(reverse('issue_list'))
        self.assertEquals(set(response.context['issues']), set([i1, i2]))

    def testClosedIssueList(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)
        i2 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_FEATURE,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)
        i3 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_SUBSCRIPTION,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        i4 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('closed_issue_list'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.context['issues']), set([i1, i2]))

    def testOrderingIssueList(self):
        now = datetime.datetime.now()
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='A',
                                  message='test',
                                  update_date=now - datetime.timedelta(3),
                                  last_comment_date=now - datetime.timedelta(3),
                                  state=ISSUE_STATE_OPEN)
        i2 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_FEATURE,
                                  subject='B',
                                  message='test',
                                  update_date=now - datetime.timedelta(1),
                                  last_comment_date=now - datetime.timedelta(1),
                                  state=ISSUE_STATE_OPEN)
        i3 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_FEATURE,
                                  subject='C',
                                  message='test',
                                  update_date=now - datetime.timedelta(2),
                                  last_comment_date=now - datetime.timedelta(2),
                                  state=ISSUE_STATE_OPEN)

        i4 = Issue.objects.create(owner_id=2,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='D',
                                  message='test',
                                  update_date=now - datetime.timedelta(4),
                                  last_comment_date=now - datetime.timedelta(4),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=200),
                                    issue=i1)
        c3 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=300),
                                    issue=i3)
        c3 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=300),
                                    issue=i3)
        c4 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=400),
                                    issue=i4)
        c4 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=400),
                                    issue=i4)
        c4 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=now - datetime.timedelta(seconds=400),
                                    issue=i4)

        Vote.objects.create(owner_id=1,
                            issue_id=i1.id)
        Vote.objects.create(owner_id=2,
                            issue_id=i1.id)
        Vote.objects.create(owner_id=1,
                            issue_id=i1.id)
        Vote.objects.create(owner_id=1,
                            issue_id=i2.id)
        Vote.objects.create(owner_id=2,
                            issue_id=i2.id)
        Vote.objects.create(owner_id=1,
                            issue_id=i3.id)
        Vote.objects.create(owner_id=2,
                            issue_id=i3.id)
        Vote.objects.create(owner_id=1,
                            issue_id=i3.id)
        Vote.objects.create(owner_id=2,
                            issue_id=i3.id)

        response = self.client.get(reverse('issue_list'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i1, i3, i4, i2])

        response = self.client.get(reverse('issue_list'),
                                   {'o': 'subject'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i1, i2, i3, i4])

        response = self.client.get(reverse('issue_list'),
                                   {'o': 'subject',
                                    'ot': 'desc'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i4, i3, i2, i1])

        response = self.client.get(reverse('issue_list'),
                                   {'o': 'author',
                                    'ot': 'desc'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i1, i3, i2, i4])

        response = self.client.get(reverse('issue_list'),
                                   {'o': 'comments',
                                    'ot': 'asc'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i2, i1, i3, i4])

        response = self.client.get(reverse('issue_list'),
                                   {'o': 'votes',
                                    'ot': 'asc'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(list(response.context['issues']), [i4, i2, i1, i3])

    def testIssueDetail(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.get(reverse('issue_detail', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['issue'], i1)

    def testGetCreateIssue(self):
        response = self.client.get(reverse('issue_add'))
        self.assertEquals(response.status_code, 200)

    def testPostCreateIssue(self):
        response = self.client.post(reverse('issue_add'),
                                    {'category': ISSUE_CATEGORY_BUG,
                                     'subject': 'test subject',
                                     'message': 'test message'})
        self.assertEquals(response.status_code, 302)
        issues = Issue.objects.all()
        self.assertEquals(len(issues), 1)
        self.assertEquals(issues[0].category, ISSUE_CATEGORY_BUG)
        self.assertEquals(issues[0].subject, 'test subject')
        self.assertEquals(issues[0].message, 'test message')
        self.assertEquals(issues[0].state, ISSUE_STATE_OPEN)
        self.assertEquals(issues[0].owner_id, 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("An issue has been opened")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testGetEditIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('issue_edit', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostEditIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.post(reverse('issue_edit', kwargs={'id': i1.id}),
                                    {'category': ISSUE_CATEGORY_FEATURE,
                                     'subject': 'test subject2',
                                     'message': 'test message2'})
        self.assertEquals(response.status_code, 302)
        issues = Issue.objects.all()
        self.assertEquals(len(issues), 1)
        self.assertEquals(issues[0].category, ISSUE_CATEGORY_FEATURE)
        self.assertEquals(issues[0].subject, 'test subject2')
        self.assertEquals(issues[0].message, 'test message2')
        self.assertEquals(issues[0].state, ISSUE_STATE_OPEN)
        self.assertEquals(issues[0].owner_id, 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("An issue has been updated")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testGetDeleteIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.get(reverse('issue_delete', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostDeleteIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.post(reverse('issue_delete', kwargs={'id': i1.id}),
                                   {'delete': 'Ok'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(len(Issue.objects.all()), 0)

    def testGetCloseIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        response = self.client.get(reverse('issue_close', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostCloseIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)
        Vote.objects.create(owner_id=1,
                            issue_id=i1.id)
        response = self.client.post(reverse('issue_close', kwargs={'id': i1.id}),
                                    {'message': 'Closed'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Issue.objects.get(pk=i1.id).state, ISSUE_STATE_CLOSED)
        self.assertEquals(i1.comment_set.count(), 1)
        self.assertEquals(len(Vote.objects.all()), 0)

    def testGetReopenIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)
        response = self.client.get(reverse('issue_reopen', kwargs={'id': i1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostReopenIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.post(reverse('issue_reopen', kwargs={'id': i1.id}),
                                    {'message': 'Reopen'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Issue.objects.get(pk=i1.id).state, ISSUE_STATE_OPEN)
        self.assertEquals(i1.comment_set.count(), 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("An issue has been reopened")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testCommentIssue(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.comment_set.count(), 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A comment has been added")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testCommentNotification(self):
        user3 = User.objects.create_user('test_user3', 'test3@example.com', 'test')

        i1 = Issue.objects.create(owner=user3,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c2 = Comment.objects.create(owner=user3,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c3 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c4 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c5 = Comment.objects.create(owner=None,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)

        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})

        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A comment has been added")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])
        self.assertEquals(mail.outbox[1].subject, ugettext('A new comment has been added on issue #%(id)d') % {'id': i1.id})
        self.assertEquals(mail.outbox[2].subject, ugettext('A new comment has been added on issue #%(id)d') % {'id': i1.id})
        recipients = [mail.outbox[1].to[0], mail.outbox[2].to[0]]
        self.assertEquals(set(recipients), set(['test2@example.com', 'test3@example.com']))

    def testCommentNotificationRegardingNotificationSettings(self):
        user3 = User.objects.create_user('test_user3', 'test3@example.com', 'test')
        notification = user3.notification
        notification.notify_bug_comments = False
        notification.save()

        i1 = Issue.objects.create(owner=user3,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c2 = Comment.objects.create(owner=user3,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c3 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c4 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c5 = Comment.objects.create(owner=None,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)

        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})

        self.assertEquals(len(mail.outbox), 2)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A comment has been added")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])
        self.assertEquals(mail.outbox[1].subject, ugettext('A new comment has been added on issue #%(id)d') % {'id': i1.id})
        recipients = [mail.outbox[1].to[0]]
        self.assertEquals(set(recipients), set(['test2@example.com']))

    def testCommentNotificationWithDeletedIssueOwner(self):
        user3 = User.objects.create_user('test_user3', 'test3@example.com', 'test')

        i1 = Issue.objects.create(owner=None,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c2 = Comment.objects.create(owner=user3,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c3 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c4 = Comment.objects.create(owner_id=2,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        c5 = Comment.objects.create(owner=None,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)

        response = self.client.post(reverse('comment_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})

        self.assertEquals(len(mail.outbox), 3)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A comment has been added")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])
        self.assertEquals(mail.outbox[1].subject, ugettext('A new comment has been added on issue #%(id)d') % {'id': i1.id})
        self.assertEquals(mail.outbox[2].subject, ugettext('A new comment has been added on issue #%(id)d') % {'id': i1.id})
        recipients = [mail.outbox[1].to[0], mail.outbox[2].to[0]]
        self.assertEquals(set(recipients), set(['test2@example.com', 'test3@example.com']))

    def testGetEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.get(reverse('comment_edit', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostEditComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_edit', kwargs={'id': c1.id}),
                                    {'message': 'comment 2'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.get(pk=c1.id).message, 'comment 2')
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A comment has been updated")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testGetDeleteComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.get(reverse('comment_delete', kwargs={'id': c1.id}))
        self.assertEquals(response.status_code, 200)

    def testPostDeleteComment(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        c1 = Comment.objects.create(owner_id=1,
                                    message='comment',
                                    update_date=datetime.datetime.now(),
                                    issue=i1)
        response = self.client.post(reverse('comment_delete', kwargs={'id': c1.id}),
                                    {'delete': 'Ok'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Comment.objects.count(), 0)

    def testVote(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('vote', kwargs={'issue_id': i1.id}))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.vote_count(), 1)
        self.assertEquals(Vote.objects.votes_remaining(User.objects.get(pk=1)), settings.BUGTRACKER_VOTES - 1)

    def testUnvote(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        Vote.objects.create(owner_id=1,
                            issue_id=i1.id)

        self.assertEquals(i1.vote_count(), 1)
        response = self.client.get(reverse('unvote', kwargs={'issue_id': i1.id}))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.vote_count(), 0)
        self.assertEquals(Vote.objects.votes_remaining(User.objects.get(pk=1)), settings.BUGTRACKER_VOTES)

    def testCantVoteIfNoVotes(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        for i in range(settings.BUGTRACKER_VOTES):
            Vote.objects.create(owner_id=1,
                                issue_id=i1.id)

        self.assertEquals(i1.vote_count(), settings.BUGTRACKER_VOTES)
        response = self.client.get(reverse('vote', kwargs={'issue_id': i1.id}))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.vote_count(), settings.BUGTRACKER_VOTES)

    def testCantVoteIfClosed(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_CLOSED)

        response = self.client.get(reverse('vote', kwargs={'issue_id': i1.id}))
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.vote_count(), 0)

class MessageTest(TestCase):
    fixtures = ['test_users']

    def setUp(self):
        self.client.login(username='test', password='test')

    def testPostCreateMessage(self):
        response = self.client.post(reverse('issue_add'),
                                    {'category': ISSUE_CATEGORY_MESSAGE,
                                     'subject': 'test subject',
                                     'message': 'test message'})
        self.assertEquals(response.status_code, 302)
        issues = Issue.objects.all()
        self.assertEquals(len(issues), 1)
        self.assertEquals(issues[0].category, ISSUE_CATEGORY_MESSAGE)
        self.assertEquals(issues[0].subject, 'test subject')
        self.assertEquals(issues[0].message, 'test message')
        self.assertEquals(issues[0].state, ISSUE_STATE_OPEN)
        self.assertEquals(issues[0].owner_id, 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("A new message has been posted")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testCommentMessage(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.post(reverse('message_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.comment_set.count(), 1)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, ugettext("An answer has been posted")))
        self.assertEquals(mail.outbox[0].to, [settings.ADMINS[0][1]])

    def testAnswerFromAdmin(self):
        i1 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_MESSAGE,
                                  subject='test subject',
                                  message='test message',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        admin = User.objects.get(pk=2)
        admin.is_superuser = True
        admin.save()
        self.client.logout()
        self.client.login(username='test2', password='test')
        response = self.client.post(reverse('message_add', kwargs={'issue_id': i1.id}),
                                    {'message': 'Comment'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(i1.comment_set.count(), 1)
        self.assertEquals(len(mail.outbox), 1)
        site = Site.objects.get_current()
        self.assertEquals(mail.outbox[0].subject, ugettext('You have received an answer on %(site_name)s') % {'site_name': site.name})
        self.assertEquals(mail.outbox[0].to, [User.objects.get(pk=1).email])
