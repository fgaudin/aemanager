from django import template
from docutils.core import publish_string
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
@stringfilter
def to_html(rst_str, autoescape=None):
    """
    Returns the rst string as html
    """
    return mark_safe(publish_string(rst_str, writer_name='html'))

to_html.needs_autoescape = True
