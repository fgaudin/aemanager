from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from notification.forms import NotificationForm
from django.contrib import messages
from django.core.urlresolvers import reverse
from core.decorators import settings_required, disabled_for_demo
from django.db.transaction import commit_on_success

@disabled_for_demo
@settings_required
@commit_on_success
def notification_edit(request):
    notification = request.user.notification

    if request.method == 'POST':
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            notification = form.save()
            messages.success(request, _('Notification settings has been saved successfully'))
            return redirect(reverse('notification_edit'))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        form = NotificationForm(instance=notification)

    return render_to_response('notification/edit.html',
                              {'active': 'settings',
                               'title': _('Notifications'),
                               'form': form},
                               context_instance=RequestContext(request))
