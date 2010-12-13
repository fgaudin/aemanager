from django import template

register = template.Library()

@register.filter
def multiply(value1, value2):
    """
    Do value1 * value2
    """
    return value1 * value2

@register.filter
def absolute(value):
    """
    Return abs(value)
    """
    return abs(value)
