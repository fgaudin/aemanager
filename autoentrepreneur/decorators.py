from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site

def subscription_required(view_func, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    decorator which redirects to subscribe page if needed
    use login_required.
    """
    def decorator(request, *args, **kwargs):
        if request.user.get_profile().is_allowed():
            return view_func(request, *args, **kwargs)
        messages.warning(request, _('Your subscription has expired. You need to subscribe again to keep using %(site_name)s') % {'site_name': Site.objects.get_current().name})
        return HttpResponseRedirect(reverse('subscribe'))
    return login_required(decorator, redirect_field_name=redirect_field_name)

"""
    actual_decorator = user_passes_test(
        lambda u: u.get_profile().is_allowed(),
        login_url='/home/subscribe/'
    )
    if function:
        return login_required(actual_decorator(function), redirect_field_name=redirect_field_name)
    return actual_decorator
"""
