from django import template

register = template.Library()

@register.filter
def format_errors(object, field_name):
    """
    Add the field label to the error message
    """
    for i in range(len(object)):
        object[i] = "%s : %s" % (unicode(field_name), object[i])
    return object
