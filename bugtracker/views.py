from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from bugtracker.models import ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE, Issue, \
    ISSUE_STATE_OPEN, Comment, Vote, ISSUE_STATE_CLOSED, \
    ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_CATEGORY_MESSAGE
from django.utils.translation import ugettext_lazy as _
from bugtracker.forms import IssueForm, CommentForm
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import commit_on_success
from django.db.models.aggregates import Count, Max
from core.decorators import settings_required
from django.core.mail import mail_admins, send_mass_mail
from django.contrib.sites.models import Site
from django.conf import settings
from core.templatetags.modeltags import display_name
import datetime

@settings_required
def issue_list(request):
    issues = Issue.objects.filter(state=ISSUE_STATE_OPEN, category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE]).annotate(votes=Count('vote')).order_by('-votes')
    return render_to_response('issue/list.html',
                              {'active': 'settings',
                               'title': _('Issue reporting'),
                               'issues': issues,
                               'state': 'open'},
                              context_instance=RequestContext(request))

@settings_required
def message_list(request):
    if request.user.is_superuser:
        issues = Issue.objects.filter(category__in=[ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_CATEGORY_MESSAGE]).annotate(last_update=Max('comment__update_date')).order_by('-last_update')
    else:
        issues = Issue.objects.filter(category__in=[ISSUE_CATEGORY_SUBSCRIPTION, ISSUE_CATEGORY_MESSAGE],
                                      owner=request.user).annotate(last_update=Max('comment__update_date')).order_by('-last_update')
    return render_to_response('message/list.html',
                              {'active': 'settings',
                               'title': _('Messages'),
                               'issues': issues},
                              context_instance=RequestContext(request))

@settings_required
def closed_issue_list(request):
    issues = Issue.objects.filter(state=ISSUE_STATE_CLOSED, category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE]).annotate(votes=Count('vote')).order_by('-votes')
    return render_to_response('issue/list.html',
                              {'active': 'settings',
                               'title': _('Issue reporting'),
                               'issues': issues,
                               'state': 'closed'},
                              context_instance=RequestContext(request))


@settings_required
@commit_on_success
def issue_create_or_edit(request, id=None):
    if id:
        title = _('Edit an issue')
        issue = get_object_or_404(Issue,
                                  pk=id,
                                  owner=request.user,
                                  category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
        mail_subject = _('An issue has been updated')
    else:
        title = _('Send an issue')
        issue = None
        mail_subject = _('An issue has been opened')

    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.update_date = datetime.datetime.now()
            issue.owner = request.user
            issue.save()
            domain = Site.objects.get_current().domain
            if issue.category in [ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE]:
                message = _('The issue has been saved successfully')
                redirect_url = reverse('issue_list')
                mail_message = _('%(issue_subject)s : %(issue_url)s') % {'issue_subject': issue.subject,
                                                                         'issue_url': 'https://%s%s' % (domain, reverse('issue_detail', kwargs={'id': issue.id}))}
            else:
                message = _('The message has been saved successfully')
                redirect_url = reverse('message_list')
                mail_subject = _('A new message has been posted')
                mail_message = _('%(message_subject)s : %(message_url)s') % {'message_subject': issue.subject,
                                                                             'message_url': 'https://%s%s' % (domain, reverse('message_detail', kwargs={'id': issue.id}))}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))
            messages.success(request, message)
            return redirect(redirect_url)
    else:
        form = IssueForm(instance=issue)

    return render_to_response('issue/edit.html',
                              {'active': 'settings',
                               'title': title,
                               'form': form},
                              context_instance=RequestContext(request))

@settings_required
@commit_on_success
def issue_close(request, id):
    issue = get_object_or_404(Issue,
                              pk=id,
                              owner=request.user,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])

    if request.method == 'POST':
        commentForm = CommentForm(request.POST)
        if commentForm.is_valid():
            comment = commentForm.save(commit=False)
            comment.update_date = datetime.datetime.now()
            comment.issue = issue
            comment.owner = request.user
            comment.save()
            issue.state = ISSUE_STATE_CLOSED
            issue.owner = request.user
            issue.save()
            Vote.objects.filter(issue=issue).delete()
            messages.success(request, _('The issue has been closed successfully'))
            return redirect(reverse('issue_list'))
    else:
        commentForm = CommentForm()

    return render_to_response('comment/edit.html',
                              {'active': 'settings',
                               'title': _('Close an issue'),
                               'form': commentForm},
                              context_instance=RequestContext(request))

@settings_required
@commit_on_success
def issue_reopen(request, id):
    issue = get_object_or_404(Issue,
                              pk=id,
                              owner=request.user,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])

    if request.method == 'POST':
        commentForm = CommentForm(request.POST)
        if commentForm.is_valid():
            comment = commentForm.save(commit=False)
            comment.update_date = datetime.datetime.now()
            comment.issue = issue
            comment.owner = request.user
            comment.save()
            issue.state = ISSUE_STATE_OPEN
            issue.owner = request.user
            issue.save()
            domain = Site.objects.get_current().domain
            mail_subject = _('An issue has been reopened')
            mail_message = _('%(issue_subject)s : %(issue_url)s') % {'issue_subject': issue.subject,
                                                                     'issue_url': 'https://%s%s' % (domain, reverse('issue_detail', kwargs={'id': issue.id}))}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))
            messages.success(request, _('The issue has been reopened successfully'))
            return redirect(reverse('issue_list'))
    else:
        commentForm = CommentForm()

    return render_to_response('comment/edit.html',
                              {'active': 'settings',
                               'title': _('Reopen an issue'),
                               'form': commentForm},
                              context_instance=RequestContext(request))

@settings_required
def issue_detail(request, id):
    issue = get_object_or_404(Issue,
                              pk=id,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
    commentForm = CommentForm()
    votes_remaining = Vote.objects.votes_remaining(request.user)
    user_votes = Vote.objects.filter(issue=issue,
                                     owner=request.user).count()

    return render_to_response('issue/detail.html',
                              {'active': 'settings',
                               'title': _('Issue'),
                               'issue': issue,
                               'commentForm': commentForm,
                               'votes_remaining': votes_remaining,
                               'user_votes': user_votes},
                              context_instance=RequestContext(request))

@settings_required
def message_detail(request, id):
    if request.user.is_superuser:
        issue = get_object_or_404(Issue, pk=id,
                                  category__in=[ISSUE_CATEGORY_MESSAGE, ISSUE_CATEGORY_SUBSCRIPTION])
    else:
        issue = get_object_or_404(Issue, pk=id,
                                  category__in=[ISSUE_CATEGORY_MESSAGE, ISSUE_CATEGORY_SUBSCRIPTION],
                                  owner=request.user)
        issue.state = ISSUE_STATE_CLOSED
        issue.save()
    commentForm = CommentForm()

    return render_to_response('message/detail.html',
                              {'active': 'settings',
                               'title': _('Message'),
                               'issue': issue,
                               'commentForm': commentForm},
                              context_instance=RequestContext(request))

@settings_required
@commit_on_success
def issue_delete(request, id):
    issue = get_object_or_404(Issue,
                              pk=id,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE],
                              owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            issue.delete()
            messages.success(request, _('The issue has been deleted successfully'))
            return redirect(reverse('issue_list'))
        else:
            return redirect(reverse('issue_detail', kwargs={'id': issue.id}))

    return render_to_response('delete.html',
                              {'active': 'settings',
                               'title': _('Delete an issue'),
                               'object_label': 'Issue "%s"' % (issue)},
                               context_instance=RequestContext(request))

@settings_required
@commit_on_success
def comment_create_or_edit(request, id=None, issue_id=None):
    if id:
        title = _('Edit a comment')
        comment = get_object_or_404(Comment,
                                    pk=id,
                                    owner=request.user,
                                    issue__category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
        issue = comment.issue
        mail_subject = _('A comment has been updated')
    else:
        title = _('Send a comment')
        comment = None
        issue = get_object_or_404(Issue,
                                  pk=issue_id,
                                  category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
        mail_subject = _('A comment has been added')

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = issue
            comment.update_date = datetime.datetime.now()
            comment.owner = request.user
            comment.save()

            domain = Site.objects.get_current().domain
            # notify admin
            mail_message = _('%(issue_subject)s : %(issue_url)s') % {'issue_subject': issue.subject,
                                                                     'issue_url': 'https://%s%s' % (domain, reverse('issue_detail', kwargs={'id': issue.id}))}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))
            # notify users who have commented except owner of this comment
            emails_to_notify = issue.emails_to_notify()
            emails_to_notify.remove(comment.owner.email)
            notification_subject = _('A new comment has been added on issue #%(id)d') % {'id': issue.id}
            notification_message = _("%(user)s wrote:") % {'user': display_name(comment.owner)}
            notification_message = "%s\n\n%s\n\n%s" % ('https://%s%s' % (domain,
                                                                         reverse('issue_detail',
                                                                                 kwargs={'id': issue.id})),
                                                       notification_message,
                                                       comment.message)
            notification_messages = []
            for email in emails_to_notify:
                notification_messages.append((notification_subject,
                                              notification_message,
                                              settings.DEFAULT_FROM_EMAIL,
                                              [email]))
            send_mass_mail(notification_messages, fail_silently=(not settings.DEBUG))

            messages.success(request, _('Your comment has been saved successfully'))
            return redirect(reverse('issue_detail', kwargs={'id': issue.id}))
    else:
        form = CommentForm(instance=comment)

    return render_to_response('comment/edit.html',
                              {'active': 'settings',
                               'title': title,
                               'form': form},
                              context_instance=RequestContext(request))

@settings_required
@commit_on_success
def comment_message_create(request, issue_id=None):
    title = _('Send a comment')
    if request.user.is_superuser:
        issue = get_object_or_404(Issue,
                                  pk=issue_id,
                                  category__in=[ISSUE_CATEGORY_MESSAGE, ISSUE_CATEGORY_SUBSCRIPTION])

    else:
        issue = get_object_or_404(Issue,
                                  pk=issue_id,
                                  category__in=[ISSUE_CATEGORY_MESSAGE, ISSUE_CATEGORY_SUBSCRIPTION],
                                  owner=request.user)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = issue
            comment.update_date = datetime.datetime.now()
            comment.owner = request.user
            comment.save()
            site = Site.objects.get_current()
            if request.user.is_superuser:
                issue.state = ISSUE_STATE_OPEN
                issue.save()
                mail_subject = _('You have received an answer on %(site_name)s') % {'site_name': site.name}
                mail_message = _("%(message_url)s\n\n%(message)s") % {'message_url': 'https://%s%s' % (site.domain, reverse('message_detail', kwargs={'id': issue.id})),
                                                                      'message': comment.message}
                issue.owner.email_user(mail_subject, mail_message)
            else:
                mail_subject = _('An answer has been posted')
                mail_message = _('%(message_subject)s : %(message_url)s') % {'message_subject': issue.subject,
                                                                             'message_url': 'https://%s%s' % (site.domain, reverse('message_detail', kwargs={'id': issue.id}))}
                mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))
            messages.success(request, _('Your comment has been saved successfully'))
            return redirect(reverse('message_detail', kwargs={'id': issue.id}))
    else:
        form = CommentForm(instance=comment)

    return render_to_response('comment/edit.html',
                              {'active': 'settings',
                               'title': title,
                               'form': form},
                              context_instance=RequestContext(request))


@settings_required
@commit_on_success
def comment_delete(request, id):
    comment = get_object_or_404(Comment,
                                pk=id,
                                owner=request.user,
                                issue__category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])

    if request.method == 'POST':
        if request.POST.get('delete'):
            comment.delete()
            messages.success(request, _('The comment has been deleted successfully'))
            return redirect(reverse('issue_detail', kwargs={'id': comment.issue.id }))
        else:
            return redirect(reverse('issue_detail', kwargs={'id': comment.issue.id}))

    return render_to_response('delete.html',
                              {'active': 'settings',
                               'title': _('Delete a comment'),
                               'object_label': 'Comment "%s"' % (comment)},
                               context_instance=RequestContext(request))

@settings_required
@commit_on_success
def vote(request, issue_id):
    issue = get_object_or_404(Issue,
                              pk=issue_id,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
    votes_remaining = Vote.objects.votes_remaining(request.user)
    if issue.state == ISSUE_STATE_OPEN:
        if votes_remaining:
            Vote.objects.create(owner=request.user,
                                issue=issue)
            messages.success(request, _('Your vote has been saved successfully'))
        else:
            messages.error(request, _("You can't vote anymore"))
    else:
        messages.error(request, _("No votes for closed issues"))
    return redirect(reverse('issue_detail', kwargs={'id': issue.id }))

@settings_required
@commit_on_success
def unvote(request, issue_id):
    issue = get_object_or_404(Issue,
                              pk=issue_id,
                              category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
    votes = Vote.objects.filter(owner=request.user,
                                issue=issue)
    if len(votes):
        votes[0].delete()
    messages.success(request, _('Your vote has been removed successfully'))
    return redirect(reverse('issue_detail', kwargs={'id': issue.id }))
