from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.template.context import RequestContext
from contact.forms import ContactForm, AddressForm, PhoneNumberForm, \
    ContactSearchForm
from contact.models import Contact, PhoneNumber, CONTACT_TYPE_PERSON, \
    CompanySearchEngine
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.transaction import commit_on_success
from django.forms.models import inlineformset_factory
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models.query_utils import Q
from core.decorators import settings_required
from autoentrepreneur.decorators import subscription_required
from django.http import HttpResponse
from django.utils import simplejson
from django.db.models.aggregates import Max

@settings_required
@subscription_required
def contact_detail(request, id):
    contact = get_object_or_404(Contact, pk=id, owner=request.user)

    return render_to_response('contact/detail.html',
                              {'active': 'contact',
                               'title': unicode(contact),
                               'contact': contact},
                               context_instance=RequestContext(request))


@settings_required
@subscription_required
@commit_on_success
def contact_create_or_edit(request, id=None):
    if id:
        title = _('Edit a contact')
        contact = get_object_or_404(Contact, pk=id, owner=request.user)
        address = contact.address
    else:
        title = _('Add a contact')
        contact = None
        address = None

    company_search_engine = CompanySearchEngine.objects.get_current()

    PhoneNumberFormSet = inlineformset_factory(Contact,
                                               PhoneNumber,
                                               form=PhoneNumberForm,
                                               fk_name="contact",
                                               extra=1)

    contacts = Contact.objects.filter(owner=request.user)
    if contact:
        contacts = contacts.exclude(pk=contact.id)

    if request.method == 'POST':
        contactForm = ContactForm(request.POST, instance=contact, prefix="contact")
        contactForm.fields['contacts'].queryset = contacts
        addressForm = AddressForm(request.POST, instance=address, prefix="address")
        phonenumberformset = PhoneNumberFormSet(request.POST, instance=contact)

        if contactForm.is_valid() and addressForm.is_valid() and phonenumberformset.is_valid():
            user = request.user
            address = addressForm.save(commit=False)
            address.save(user=user)
            contact = contactForm.save(commit=False)
            contact.address = address
            contact.save(user=user)
            contactForm.save_m2m()
            for phonenumberform in phonenumberformset.forms:
                phonenumber = phonenumberform.save(commit=False)
                if phonenumber.type:
                    phonenumber.contact = contact
                    phonenumber.save(user=user)

            for deleted_phonenumberrowform in phonenumberformset.deleted_forms:
                deleted_phonenumberrowform.cleaned_data['ownedobject_ptr'].delete()

            messages.success(request, _('The contact has been saved successfully'))
            return redirect(reverse('contact_detail', kwargs={'id': contact.id}))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        contactForm = ContactForm(instance=contact, prefix="contact")
        contactForm.fields['contacts'].queryset = contacts
        addressForm = AddressForm(instance=address, prefix="address")
        phonenumberformset = PhoneNumberFormSet(instance=contact)

    return render_to_response('contact/edit.html',
                              {'active': 'contact',
                               'title': title,
                               'contactForm': contactForm,
                               'addressForm': addressForm,
                               'phonenumberformset': phonenumberformset,
                               'search_engine': company_search_engine},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
def contact_search(request):
    user = request.user

    o = request.GET.get('o', 'name')
    if o not in ('name', 'email', 'phonenumber'):
        o = 'name'
    if o == 'phonenumber':
        order = 'phonenumber__number'
    else:
        order = o

    ot = request.GET.get('ot', 'asc')
    if ot not in ('asc', 'desc'):
        ot = 'asc'
    if ot == 'desc':
        direction = '-'
    else:
        direction = ''

    contact_list = Contact.objects.filter(owner=user).distinct()
    contact_list = contact_list.order_by(direction + order)

    # search criteria
    form = ContactSearchForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        contact_list = contact_list.filter(Q(name__icontains=data['name']) | Q(firstname__icontains=data['name']))
        contact_list = contact_list.filter(email__icontains=data['email'])
        if data['phonenumber']:
            contact_list = contact_list.filter(phonenumber__number__icontains=data['phonenumber'])

    else:
        data = {'name': '',
                'email': '',
                'phonenumber': ''}

    paginator = Paginator(contact_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        contacts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        contacts = paginator.page(paginator.num_pages)


    return render_to_response('contact/search.html',
                              {'active': 'contact',
                               'title': _('Search contact'),
                               'contacts': contacts,
                               'o': o,
                               'ot': ot,
                               'form': form,
                               'search_criteria': data},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
@commit_on_success
def contact_delete(request, id):
    contact = get_object_or_404(Contact, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            address = contact.address
            contact.delete()
            address.delete()
            messages.success(request, _('The contact has been deleted successfully'))
            return redirect(reverse('contact_search'))
        else:
            return redirect(reverse('contact_detail', kwargs={'id': contact.id}))

    return render_to_response('delete.html',
                              {'active': 'contact',
                               'title': _('Delete a contact'),
                               'object_label': 'contact "%s"' % (contact)},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
def contact_ajax_search(request):
    term = request.GET.get('term')
    user = request.user
    data = list(Contact.objects.filter(owner=user, name__icontains=term)
      .extra(select={'label': 'name',
                     'value':'name'})
      .values('id', 'name', 'address__street', 'address__zipcode', 'address__city', 'address__country__id', 'label', 'value'))

    return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')
