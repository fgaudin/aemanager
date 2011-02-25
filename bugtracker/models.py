from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.text import truncate_html_words
from django.conf import settings

ISSUE_CATEGORY_BUG = 1
ISSUE_CATEGORY_FEATURE = 2
ISSUE_CATEGORY_SUBSCRIPTION = 3
ISSUE_CATEGORY_MESSAGE = 4
ISSUE_CATEGORY = ((ISSUE_CATEGORY_BUG, _('Bug')),
                  (ISSUE_CATEGORY_FEATURE, _('Feature request')),
                  (ISSUE_CATEGORY_SUBSCRIPTION, _('Subscription')),
                  (ISSUE_CATEGORY_MESSAGE, _('Message / question')))

ISSUE_STATE_OPEN = 1
ISSUE_STATE_CLOSED = 2
ISSUE_STATE = ((ISSUE_STATE_OPEN, _('Open')),
               (ISSUE_STATE_CLOSED, _('Closed')))

class IssueManager(models.Manager):
    def unread_messages(self, user):
        return self.filter(category__in=[ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_CATEGORY_MESSAGE],
                           owner=user,
                           state=ISSUE_STATE_OPEN).count()

class Issue(models.Model):
    owner = models.ForeignKey(User, verbose_name=_('User'), null=True)
    category = models.IntegerField(verbose_name=_('Category'), choices=ISSUE_CATEGORY, help_text=_('Only bugs and features are public'), db_index=True)
    subject = models.CharField(verbose_name=_('Subject'), max_length=255)
    message = models.TextField(verbose_name=_('Message'))
    update_date = models.DateTimeField(verbose_name=_('Update date'))
    state = models.IntegerField(verbose_name=_('State'), choices=ISSUE_STATE, default=ISSUE_STATE_OPEN, db_index=True)

    objects = IssueManager()

    def __unicode__(self):
        return '%s' % (self.subject)

    def vote_count(self):
        return self.vote_set.count()

    def is_open(self):
        return self.state == ISSUE_STATE_OPEN

    def is_closed(self):
        return self.state == ISSUE_STATE_CLOSED

class Comment(models.Model):
    owner = models.ForeignKey(User, verbose_name=_('User'), null=True)
    message = models.TextField(verbose_name=_('Message'))
    issue = models.ForeignKey(Issue, verbose_name=_('Issue'))
    update_date = models.DateTimeField(verbose_name=_('Update date'))

    class Meta:
        ordering = ['update_date']

    def __unicode__(self):
        return '%s' % (truncate_html_words(self.message, 5))

class VoteManager(models.Manager):
    def votes_remaining(self, user):
        return settings.BUGTRACKER_VOTES - self.filter(owner=user).count()

class Vote(models.Model):
    issue = models.ForeignKey(Issue, verbose_name=_('Issue'))
    owner = models.ForeignKey(User, verbose_name=_('User'))

    objects = VoteManager()
