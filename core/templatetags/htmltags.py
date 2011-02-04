from django import template
from docutils.core import publish_string
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django.utils.html import escape
import re

register = template.Library()

def replace_filtered_tags(str):
    formated_str = str
    formated_str = formated_str.replace('&lt;h1&gt;', '<h1>')
    formated_str = formated_str.replace('&lt;/h1&gt;', '</h1>')
    formated_str = formated_str.replace('&lt;h2&gt;', '<h2>')
    formated_str = formated_str.replace('&lt;/h2&gt;', '</h2>')
    formated_str = formated_str.replace('&lt;h3&gt;', '<h3>')
    formated_str = formated_str.replace('&lt;/h3&gt;', '</h3>')
    formated_str = formated_str.replace('&lt;h4&gt;', '<h4>')
    formated_str = formated_str.replace('&lt;/h4&gt;', '</h4>')
    formated_str = formated_str.replace('&lt;h5&gt;', '<h5>')
    formated_str = formated_str.replace('&lt;/h5&gt;', '</h5>')
    formated_str = formated_str.replace('&lt;h6&gt;', '<h6>')
    formated_str = formated_str.replace('&lt;/h6&gt;', '</h6>')

    formated_str = formated_str.replace('&lt;div&gt;', '<div>')
    formated_str = formated_str.replace('&lt;/div&gt;', '</div>')
    formated_str = formated_str.replace('&lt;p&gt;', '<p>')
    formated_str = formated_str.replace('&lt;/p&gt;', '</p>')
    formated_str = formated_str.replace('&lt;br&gt;', '<br>')
    formated_str = formated_str.replace('&lt;address&gt;', '<address>')
    formated_str = formated_str.replace('&lt;/address&gt;', '</address>')
    formated_str = formated_str.replace('&lt;pre&gt;', '<pre>')
    formated_str = formated_str.replace('&lt;/pre&gt;', '</pre>')

    formated_str = formated_str.replace('&lt;strong&gt;', '<strong>')
    formated_str = formated_str.replace('&lt;/strong&gt;', '</strong>')
    formated_str = formated_str.replace('&lt;em&gt;', '<em>')
    formated_str = formated_str.replace('&lt;/em&gt;', '</em>')
    formated_str = formated_str.replace('&lt;strike&gt;', '<strike>')
    formated_str = formated_str.replace('&lt;/strike&gt;', '</strike>')
    formated_str = formated_str.replace('&lt;sub&gt;', '<sub>')
    formated_str = formated_str.replace('&lt;/sub&gt;', '</sub>')
    formated_str = formated_str.replace('&lt;sup&gt;', '<sup>')
    formated_str = formated_str.replace('&lt;/sup&gt;', '</sup>')
    formated_str = formated_str.replace('&lt;span style=&quot;text-decoration:underline&quot;&gt;', '<span style="text-decoration:underline">')
    formated_str = formated_str.replace('&lt;/span&gt;', '</span>')

    formated_str = formated_str.replace('&lt;ol&gt;', '<ol>')
    formated_str = formated_str.replace('&lt;/ol&gt;', '</ol>')
    formated_str = formated_str.replace('&lt;ul&gt;', '<ul>')
    formated_str = formated_str.replace('&lt;/ul&gt;', '</ul>')
    formated_str = formated_str.replace('&lt;li&gt;', '<li>')
    formated_str = formated_str.replace('&lt;/li&gt;', '</li>')

    formated_str = re.sub('&lt;table(.*?)&gt;', '<table>', formated_str)
    formated_str = formated_str.replace('&lt;/table&gt;', '</table>')
    formated_str = formated_str.replace('&lt;tbody&gt;', '<tbody>')
    formated_str = formated_str.replace('&lt;/tbody&gt;', '</tbody>')
    formated_str = formated_str.replace('&lt;tr&gt;', '<tr>')
    formated_str = formated_str.replace('&lt;/tr&gt;', '</tr>')
    formated_str = formated_str.replace('&lt;td&gt;', '<td>')
    formated_str = formated_str.replace('&lt;/td&gt;', '</td>')

    formated_str = formated_str.replace('&amp;nbsp;', '&nbsp;')
    return formated_str

@register.filter
@stringfilter
def to_html(str, autoescape=None):
    """
    Returns string as html filtering only some tags
    """
    str = escape(str)
    return mark_safe(replace_filtered_tags(str))

to_html.needs_autoescape = True
