from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils.functional import wraps
from django.utils.decorators import available_attrs

def settings_required(view_func, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    decorator which redirects to settings page if mandatory
    values are not set, use login_required.
    """
    def decorator(request, *args, **kwargs):
        if request.user.get_profile().settings_defined():
            return view_func(request, *args, **kwargs)
        messages.info(request, _('You need to fill these informations to continue'))
        return HttpResponseRedirect(reverse('settings_edit'))
    return login_required(wraps(view_func, assigned=available_attrs(view_func))(decorator), redirect_field_name=redirect_field_name)
