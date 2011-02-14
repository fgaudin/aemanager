from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test, login_required

def subscription_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    decorator which redirects to subscribe page if needed
    use login_required.
    """
    actual_decorator = user_passes_test(
        lambda u: u.get_profile().is_allowed(),
        login_url='/home/subscribe/'
    )
    if function:
        return login_required(actual_decorator(function), redirect_field_name=redirect_field_name)
    return actual_decorator
