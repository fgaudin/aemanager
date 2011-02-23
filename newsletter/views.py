from django.contrib.admin.views.decorators import staff_member_required
from newsletter.forms import EmailUsersForm
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from newsletter.models import Message
from django.db.transaction import commit_on_success
import datetime

@staff_member_required
@commit_on_success
def email_users(request, message_id=None):
    message_list = Message.objects.all()

    message = None
    if message_id:
        message = get_object_or_404(Message, pk=message_id)

    if request.method == 'POST':
        form = EmailUsersForm(request.POST, instance=message)
        if form.is_valid():
            message = form.save(commit=False)
            message.update_datetime = datetime.datetime.now()
            message.save()
            messages.success(request, _('Message stored successfully for later sending.'))
            return redirect(reverse('email_users'))
    else:
        form = EmailUsersForm(instance=message)
    return render_to_response('newsletter/email_users.html',
                              {'title': _('Email users'),
                               'form': form,
                               'message_list': message_list},
                              context_instance=RequestContext(request))

@staff_member_required
@commit_on_success
def email_delete(request, id):
    message = get_object_or_404(Message, pk=id)

    if request.method == 'POST':
        if request.POST.get('delete'):
            message.delete()
            messages.success(request, _('The message has been deleted successfully'))
            return redirect(reverse('email_users'))
        else:
            return redirect(reverse('email_users'))

    return render_to_response('delete.html',
                              {'active': 'account',
                               'title': _('Delete the message'),
                               'object_label': _('the message "%(subject)s"') % {'subject': message.subject}},
                               context_instance=RequestContext(request))
