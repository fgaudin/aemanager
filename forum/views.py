from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from forum.forms import TopicForm, MessageForm
from django.contrib import messages
from forum.models import Topic, MessageNotification
from core.decorators import settings_required
from django.db.transaction import commit_on_success
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, InvalidPage
import datetime
from django.db.models.aggregates import Max
from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.conf import settings

@settings_required
def topic_list(request):
    topic_list = Topic.objects.all().annotate(last_date=Max('messages__creation_date')).order_by('-last_date')

    paginator = Paginator(topic_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        topics = paginator.page(page)
    except (EmptyPage, InvalidPage):
        topics = paginator.page(paginator.num_pages)

    return render_to_response('topic/list.html',
                              {'active': 'help',
                               'title': _('Forum'),
                               'topics': topics},
                               context_instance=RequestContext(request))

@settings_required
@commit_on_success
def topic_create(request):
    if request.method == 'POST':
        topicForm = TopicForm(request.POST, prefix="topic")
        messageForm = MessageForm(request.POST, prefix="message")
        if topicForm.is_valid() and messageForm.is_valid():
            topic = topicForm.save(commit=False)
            topic.author = request.user
            topic.creation_date = datetime.datetime.now()
            topic.save()
            message = messageForm.save(commit=False)
            message.author = request.user
            message.creation_date = datetime.datetime.now()
            message.topic = topic
            message.save()

            domain = Site.objects.get_current().domain
            mail_subject = _('A new topic has been posted')
            mail_message = _('%(topic)s : %(topic_url)s') % {'topic': topic.title,
                                                             'topic_url': 'https://%s%s' % (domain, reverse('topic_detail', kwargs={'id': topic.id}))}
            mail_admins(mail_subject, mail_message, fail_silently=(not settings.DEBUG))

            messages.success(request, _('The topic has been saved successfully'))
            return redirect(reverse('topic_detail', kwargs={'id': topic.id}))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        topicForm = TopicForm(prefix="topic")
        messageForm = MessageForm(prefix="message")

    return render_to_response('topic/create.html',
                              {'active': 'help',
                               'title': _('New topic'),
                               'topicForm': topicForm,
                               'messageForm': messageForm},
                               context_instance=RequestContext(request))

@settings_required
def topic_detail(request, id):
    topic = get_object_or_404(Topic, pk=id)
    topic.views += 1
    topic.save()
    title = unicode(topic)

    message_list = topic.messages.all()

    paginator = Paginator(message_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        answers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        answers = paginator.page(paginator.num_pages)


    if request.method == 'POST':
        messageForm = MessageForm(request.POST, prefix="message")
        if messageForm.is_valid():
            message = messageForm.save(commit=False)
            message.author = request.user
            message.creation_date = datetime.datetime.now()
            message.topic = topic
            message.save()

            MessageNotification.objects.filter(message__topic=topic).delete()
            MessageNotification.objects.create(message=message)

            messages.success(request, _('The message has been saved successfully'))
            return redirect("%s?page=-1#last" % (reverse('topic_detail', kwargs={'id': topic.id})))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        messageForm = MessageForm(prefix="message")

    return render_to_response('topic/detail.html',
                              {'active': 'help',
                               'title': title,
                               'topic': topic,
                               'answers': answers,
                               'messageForm': messageForm},
                               context_instance=RequestContext(request))
