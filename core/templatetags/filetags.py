import os
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def basename(path):
    """
    Returns os.path.basename from a path
    """
    return os.path.basename(path)
