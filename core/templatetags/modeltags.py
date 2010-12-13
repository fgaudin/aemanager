from django import template

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
