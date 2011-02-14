from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from bugtracker.models import ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE, Issue, \
    ISSUE_STATE_OPEN, Comment, Vote, ISSUE_STATE_CLOSED
from django.utils.translation import ugettext_lazy as _
from bugtracker.forms import IssueForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import commit_on_success
from django.conf import settings
from django.db.models.aggregates import Count
from core.decorators import settings_required
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
        issue = get_object_or_404(Issue, pk=id, owner=request.user)
    else:
        title = _('Send an issue')
        issue = None

    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.update_date = datetime.datetime.now()
            issue.save(user=request.user)
            messages.success(request, _('The issue has been saved successfully'))
            return redirect(reverse('issue_list'))
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
    issue = get_object_or_404(Issue, pk=id, owner=request.user)

    if request.method == 'POST':
        commentForm = CommentForm(request.POST)
        if commentForm.is_valid():
            comment = commentForm.save(commit=False)
            comment.update_date = datetime.datetime.now()
            comment.issue = issue
            comment.save(user=request.user)
            issue.state = ISSUE_STATE_CLOSED
            issue.save(user=request.user)
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
    issue = get_object_or_404(Issue, pk=id, owner=request.user)

    if request.method == 'POST':
        commentForm = CommentForm(request.POST)
        if commentForm.is_valid():
            comment = commentForm.save(commit=False)
            comment.update_date = datetime.datetime.now()
            comment.issue = issue
            comment.save(user=request.user)
            issue.state = ISSUE_STATE_OPEN
            issue.save(user=request.user)
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
    issue = get_object_or_404(Issue, pk=id, category__in=[ISSUE_CATEGORY_BUG, ISSUE_CATEGORY_FEATURE])
    commentForm = CommentForm()
    votes_remaining = Vote.objects.votes_remaining(request.user)
    user_votes = Vote.objects.filter(issue=issue,
                                   user=request.user).count()

    return render_to_response('issue/detail.html',
                              {'active': 'settings',
                               'title': _('Issue'),
                               'issue': issue,
                               'commentForm': commentForm,
                               'votes_remaining': votes_remaining,
                               'user_votes': user_votes},
                              context_instance=RequestContext(request))

@settings_required
@commit_on_success
def issue_delete(request, id):
    issue = get_object_or_404(Issue, pk=id, owner=request.user)

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
        comment = get_object_or_404(Comment, pk=id, owner=request.user)
        issue = comment.issue
    else:
        title = _('Send a comment')
        comment = None
        issue = get_object_or_404(Issue, pk=issue_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.issue = issue
            comment.update_date = datetime.datetime.now()
            comment.save(user=request.user)
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
def comment_delete(request, id):
    comment = get_object_or_404(Comment, pk=id, owner=request.user)

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
    issue = get_object_or_404(Issue, pk=issue_id)
    votes_remaining = Vote.objects.votes_remaining(request.user)
    if issue.state == ISSUE_STATE_OPEN:
        if votes_remaining:
            Vote.objects.create(user=request.user,
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
    issue = get_object_or_404(Issue, pk=issue_id)
    votes = Vote.objects.filter(user=request.user,
                                issue=issue)
    if len(votes):
        votes[0].delete()
    messages.success(request, _('Your vote has been removed successfully'))
    return redirect(reverse('issue_detail', kwargs={'id': issue.id }))
