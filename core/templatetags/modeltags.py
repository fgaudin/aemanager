from django import template
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def verbose_name(object, field_name):
    """
    Returns the verbose name of the field of the object
    """
    return object._meta.get_field_by_name(field_name)[0].verbose_name

@register.filter
def value(object, field_name):
    """
    Returns the value of the field of the object
    """
    return getattr(object, field_name)

@register.filter
def display_name(object):
    """
    Returns the display name of user :
    Firstname L. (first letter of last name)
    if user deleted : user deleted
    if admin : Firstname Lastname<br /><strong>Administrateur</strong>
    """
    if type(object) == User:
        if object.is_superuser:
            return mark_safe('%s %s<br /><strong>%s</strong>' % (object.first_name,
                                                object.last_name,
                                                _('Administrator')))
        else:
            return '%s %s.' % (object.first_name,
                               object.last_name[0])
    else:
        return mark_safe('<span class="user-deleted">%s</span>' % (ugettext('User deleted')))
