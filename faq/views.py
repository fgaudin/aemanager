from django.utils.translation import ugettext_lazy as _
from faq.models import Category
from django.shortcuts import render_to_response
from django.template.context import RequestContext

def faq_list(request):
    categories = Category.objects.all()

    return render_to_response('faq/list.html',
                              {'active': 'help',
                               'title': _('FAQ'),
                               'categories': categories},
                               context_instance=RequestContext(request))
