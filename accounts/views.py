# coding=utf-8

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext
from accounts.forms import ExpenseForm, InvoiceRowForm, InvoiceForm
from accounts.models import Expense, Invoice, InvoiceRow, InvoiceRowAmountError, \
    InvoiceIdNotUniqueError, INVOICE_STATE_PAID
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.formats import localize
from django.db.transaction import commit_on_success
from contact.models import Contact
from django.forms.models import inlineformset_factory
from project.models import Proposal, PROPOSAL_STATE_BALANCED, \
    PROPOSAL_STATE_ACCEPTED
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from custom_canvas import NumberedCanvas
from core.decorators import settings_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from autoentrepreneur.decorators import subscription_required
from django.db.models.query_utils import Q
import datetime
from reportlab.platypus import Paragraph, Frame, Spacer, BaseDocTemplate, PageTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

@settings_required
@subscription_required
def expense_list(request):
    user = request.user
    expense_list = Expense.objects.filter(owner=user).order_by('-date', '-reference')
    years = range(datetime.date.today().year, user.get_profile().creation_date.year - 1, -1)

    paginator = Paginator(expense_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        expenses = paginator.page(page)
    except (EmptyPage, InvalidPage):
        expenses = paginator.page(paginator.num_pages)

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
    else:
        form = ExpenseForm(initial={'date': localize(datetime.date.today())})
    return render_to_response('expense/list.html',
                              {'active': 'accounts',
                               'title': _('Expenses'),
                               'form': form,
                               'expenses': expenses,
                               'years': years},
                              context_instance=RequestContext(request))

@settings_required
@subscription_required
@commit_on_success
def expense_add(request):
    response = {'error': 'ko'}
    if request.POST:
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.owner = request.user
            expense.save()
            response['error'] = 'ok'
            response['id'] = expense.id
            response['date'] = localize(expense.date)
            response['reference'] = expense.reference
            response['supplier'] = expense.supplier
            response['amount'] = localize(expense.amount)
            response['payment_type'] = expense.payment_type
            response['payment_type_label'] = expense.get_payment_type_display()
            response['description'] = expense.description
        else:
            response['error_msg'] = []
            for key, msg in form.errors.items():
                response['error_msg'].append("%s : %s" % (unicode(form[key].label), " ".join(msg)))

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

@settings_required
@subscription_required
@commit_on_success
def expense_edit(request):
    id = request.GET.get('id')
    expense = get_object_or_404(Expense, pk=id, owner=request.user)
    response = {'error': 'ko'}
    if request.POST:
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense = form.save()
            response['error'] = 'ok'
            response['id'] = expense.id
            response['date'] = localize(expense.date)
            response['reference'] = expense.reference
            response['supplier'] = expense.supplier
            response['amount'] = localize(expense.amount)
            response['payment_type'] = expense.payment_type
            response['payment_type_label'] = expense.get_payment_type_display()
            response['description'] = expense.description
        else:
            response['error_msg'] = []
            for key, msg in form.errors.items():
                response['error_msg'].append("%s : %s" % (unicode(form[key].label), " ".join(msg)))


    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

@settings_required
@subscription_required
@commit_on_success
def expense_delete(request):
    response = {'error': 'ko'}
    if request.POST:
        id = int(request.POST.get('id'))
        expense = get_object_or_404(Expense, pk=id, owner=request.user)
        expense.delete()
        response['error'] = 'ok'
        response['id'] = id

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

@settings_required
@subscription_required
def expense_list_export(request):
    user = request.user

    def expense_list_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        PAGE_WIDTH = defaultPageSize[0]
        footer_text = "%s %s - SIRET : %s - %s, %s %s" % (user.first_name,
                                                          user.last_name,
                                                          user.get_profile().company_id,
                                                          user.get_profile().address.street,
                                                          user.get_profile().address.zipcode,
                                                          user.get_profile().address.city)
        if user.get_profile().address.country:
            footer_text = footer_text + ", %s" % (user.get_profile().address.country)
        canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.5 * inch, footer_text)
        canvas.restoreState()

    year = int(request.GET.get('year'))
    expenses = Expense.objects.filter(owner=user,
                                      date__year=year).order_by('date')
    filename = ugettext('purchase_book_%(year)d.pdf') % {'year': year}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    doc = BaseDocTemplate(response, title=ugettext('Purchase book %(year)d') % {'year': year})
    frameT = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frameT, onPage=expense_list_footer), ])

    styleH = ParagraphStyle({})
    styleH.fontSize = 14
    styleH.borderColor = colors.black
    styleH.alignment = TA_CENTER

    p = Paragraph(ugettext('Purchase book %(year)d') % {'year': year}, styleH)
    spacer = Spacer(1 * inch, 0.5 * inch)

    data = [[ugettext('Date'), ugettext('Ref.'), ugettext('Supplier'), ugettext('Nature'), ugettext('Amount'), ugettext('Payment type')]]

    for expense in expenses:
        data.append([localize(expense.date), expense.reference, expense.supplier, expense.description, localize(expense.amount), expense.get_payment_type_display()])
    t = Table(data, [0.8 * inch, 0.9 * inch, 1.6 * inch, 1.7 * inch, 0.7 * inch, 1.2 * inch], (len(expenses) + 1) * [0.3 * inch])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                           ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                           ('ALIGN', (2, 1), (3, -1), 'LEFT'),
                           ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                           ('FONT', (0, 0), (-1, 0), 'Times-Bold'),
                           ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                           ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ]))

    story = []
    story.append(p)
    story.append(spacer)
    story.append(t)
    doc.build(story, canvasmaker=NumberedCanvas)
    return response

@settings_required
@subscription_required
def invoice_list(request):
    user = request.user
    invoices = Invoice.objects.filter(owner=user).order_by('-invoice_id')
    years = range(datetime.date.today().year, user.get_profile().creation_date.year - 1, -1)
    return render_to_response('invoice/list.html',
                              {'active': 'accounts',
                               'title': _('Invoices'),
                               'invoices': invoices,
                               'years': years},
                              context_instance=RequestContext(request))

@settings_required
@subscription_required
def invoice_list_export(request):
    user = request.user

    def invoice_list_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        PAGE_WIDTH = defaultPageSize[0]
        footer_text = "%s %s - SIRET : %s - %s, %s %s" % (user.first_name,
                                                          user.last_name,
                                                          user.get_profile().company_id,
                                                          user.get_profile().address.street,
                                                          user.get_profile().address.zipcode,
                                                          user.get_profile().address.city)
        if user.get_profile().address.country:
            footer_text = footer_text + ", %s" % (user.get_profile().address.country)
        canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.5 * inch, footer_text)
        canvas.restoreState()

    year = int(request.GET.get('year'))
    invoices = Invoice.objects.filter(owner=user,
                                      state__gte=INVOICE_STATE_PAID,
                                      paid_date__year=year).order_by('invoice_id')
    filename = ugettext('invoice_book_%(year)d.pdf') % {'year': year}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    doc = BaseDocTemplate(response, title=ugettext('Invoice book %(year)d') % {'year': year})
    frameT = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frameT, onPage=invoice_list_footer), ])

    styleH = ParagraphStyle({})
    styleH.fontSize = 14
    styleH.borderColor = colors.black
    styleH.alignment = TA_CENTER

    p = Paragraph(ugettext('Invoice book %(year)d') % {'year': year}, styleH)
    spacer = Spacer(1 * inch, 0.5 * inch)

    data = [[ugettext('Date'), ugettext('Ref.'), ugettext('Customer'), ugettext('Nature'), ugettext('Amount'), ugettext('Payment type')]]

    for invoice in invoices:
        data.append([localize(invoice.paid_date), invoice.invoice_id, invoice.customer, invoice.getNature(), localize(invoice.amount), invoice.get_payment_type_display()])
    t = Table(data, [0.8 * inch, 0.4 * inch, 2.5 * inch, 1.2 * inch, 0.8 * inch, 1.2 * inch], (len(invoices) + 1) * [0.3 * inch])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                           ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                           ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                           ('FONT', (0, 0), (-1, 0), 'Times-Bold'),
                           ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                           ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                           ]))

    story = []
    story.append(p)
    story.append(spacer)
    story.append(t)
    doc.build(story, canvasmaker=NumberedCanvas)
    return response

@settings_required
@subscription_required
@commit_on_success
def invoice_create_or_edit(request, id=None, customer_id=None, proposal_id=None):
    if id:
        title = _('Edit an invoice')
        invoice = get_object_or_404(Invoice, pk=id, owner=request.user)
        customer = invoice.customer
    else:
        title = _('Draw up an invoice')
        invoice = None
        customer = get_object_or_404(Contact, pk=customer_id, owner=request.user)

    proposal = None
    if proposal_id:
        proposal = get_object_or_404(Proposal,
                                     pk=proposal_id,
                                     project__customer=customer,
                                     owner=request.user,
                                     state__in=[PROPOSAL_STATE_ACCEPTED])

    InvoiceRowFormSet = inlineformset_factory(Invoice,
                                              InvoiceRow,
                                              form=InvoiceRowForm,
                                              fk_name="invoice",
                                              extra=1)

    filter = Q(project__customer=customer,
               state=PROPOSAL_STATE_ACCEPTED,
               owner=request.user)
    if invoice:
        filter = filter | Q(invoice_rows__invoice=invoice,
                            owner=request.user)

    proposals = Proposal.objects.filter(filter).distinct()

    if request.method == 'POST':
        invoiceForm = InvoiceForm(request.POST, instance=invoice, prefix="invoice")
        invoicerowformset = InvoiceRowFormSet(request.POST, instance=invoice)
        for invoicerowform in invoicerowformset.forms:
            invoicerowform.fields['proposal'].queryset = proposals

        if invoiceForm.is_valid() and invoicerowformset.is_valid():
            try:
                user = request.user
                invoice = invoiceForm.save(commit=False)
                invoice.customer = customer
                if invoice.paid_date:
                    invoice.state = INVOICE_STATE_PAID
                invoice.save(user=user)
                invoiceForm.save_m2m()
                for invoicerowform in invoicerowformset.forms:
                    if invoicerowform not in invoicerowformset.deleted_forms and invoicerowform.cleaned_data:
                        invoicerow = invoicerowform.save(commit=False)
                        invoicerow.invoice = invoice
                        invoicerow.save(user=user)

                        if invoicerow.balance_payments and invoice.paid_date:
                            invoicerow.proposal.state = PROPOSAL_STATE_BALANCED
                            invoicerow.proposal.save()

                for deleted_invoicerowform in invoicerowformset.deleted_forms:
                    deleted_invoicerowform.instance.delete()

                invoice.check_amounts()

                messages.success(request, _('The invoice has been saved successfully'))
                if invoice.paid_date and invoice.paid_date > datetime.date.today():
                    messages.warning(request, _("Paid date is in the future, is this normal ?"))
                if invoice.execution_begin_date and invoice.execution_end_date and invoice.execution_begin_date > invoice.execution_end_date:
                    messages.warning(request, _("Execution begin date is greater than execution end date, is this normal ?"))
                if invoice.penalty_date and invoice.penalty_date < invoice.payment_date:
                    messages.warning(request, _("Payment date is greater than penalty date, is this normal ?"))
                return redirect(reverse('invoice_detail', kwargs={'id': invoice.id}))
            except InvoiceRowAmountError:
                transaction.rollback()
                messages.error(request, _("Amounts invoiced can't be greater than proposals remaining amounts"))
            except InvoiceIdNotUniqueError:
                transaction.rollback()
                invoiceForm._errors["invoice_id"] = invoiceForm.error_class([_("Invoice id must be unique")])
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        next_invoice_id = Invoice.objects.get_next_invoice_id(request.user)
        initial_data = None
        if not invoice:
            initial_data = {'invoice_id': next_invoice_id,
                            'edition_date': datetime.datetime.now()}
            if proposal:
                initial_data['execution_begin_date'] = proposal.begin_date
                initial_data['execution_end_date'] = proposal.end_date

        invoiceForm = InvoiceForm(instance=invoice,
                                  prefix="invoice",
                                  initial=initial_data)

        initial_row_data = None
        if proposal:
            initial_row_data = []
            for proposal_row in proposal.proposal_rows.all():
                initial_row_data.append({'label': proposal_row.label,
                                         'proposal': proposal,
                                         'balance_payments': True,
                                         'category': proposal_row.category,
                                         'quantity': proposal_row.quantity,
                                         'unit_price': proposal_row.unit_price})
            InvoiceRowFormSet.extra = len(initial_row_data) + 1

        invoicerowformset = InvoiceRowFormSet(instance=invoice)
        i = 0
        for invoicerowform in invoicerowformset.forms:
            invoicerowform.fields['proposal'].queryset = proposals
            # for all rows except last
            if i < InvoiceRowFormSet.extra - 1:
                invoicerowform.initial = initial_row_data[i]
                i = i + 1


    return render_to_response('invoice/edit.html',
                              {'active': 'accounts',
                               'title': title,
                               'from_proposal': proposal,
                               'invoiceForm': invoiceForm,
                               'invoicerowformset': invoicerowformset},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
def invoice_detail(request, id):
    invoice = get_object_or_404(Invoice, pk=id, owner=request.user)

    return render_to_response('invoice/detail.html',
                              {'active': 'accounts',
                               'title': _('Invoice for %s') % (invoice.customer),
                               'invoice': invoice},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
@commit_on_success
def invoice_delete(request, id):
    invoice = get_object_or_404(Invoice, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            invoice.delete()
            messages.success(request, _('The invoice has been deleted successfully'))
            return redirect(reverse('index'))
        else:
            return redirect(reverse('invoice_detail', kwargs={'id': invoice.id}))

    return render_to_response('delete.html',
                              {'active': 'accounts',
                               'title': _('Delete an invoice'),
                               'object_label': "invoice #%d" % (invoice.id)},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
def invoice_download(request, id):
    user = request.user
    invoice = get_object_or_404(Invoice, pk=id, owner=user)

    response = HttpResponse(mimetype='application/pdf')
    invoice.to_pdf(user, response)
    return response
