from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.filter
@stringfilter
def replace_quote(str, autoescape=None):
    """
    Returns string as html filtering only some tags
    """
    str = escape(str)
    str = str.replace('[quote]', '<quote>')
    str = str.replace('[/quote]', '</quote>')
    return mark_safe(str)

replace_quote.needs_autoescape = True
