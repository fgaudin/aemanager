from django.test import TestCase
from bugtracker.models import ISSUE_CATEGORY_BUG, ISSUE_STATE_OPEN, Issue, \
    ISSUE_CATEGORY_FEATURE, ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_STATE_CLOSED, \
    Vote, Comment
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
import datetime

class BugTrackerTest(TestCase):
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

        i3 = Issue.objects.create(owner_id=1,
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

        i3 = Issue.objects.create(owner_id=1,
                                  category=ISSUE_CATEGORY_BUG,
                                  subject='test',
                                  message='test',
                                  update_date=datetime.datetime.now(),
                                  state=ISSUE_STATE_OPEN)

        response = self.client.get(reverse('closed_issue_list'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(set(response.context['issues']), set([i1, i2]))

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
        Vote.objects.create(user_id=1,
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

        Vote.objects.create(user_id=1,
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
            Vote.objects.create(user_id=1,
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
