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
from django.db.models.aggregates import Max
from custom_canvas import NumberedCanvas
from core.decorators import settings_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from autoentrepreneur.decorators import subscription_required
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
                               'expenses': expenses},
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
        data.append([localize(invoice.paid_date), invoice.invoice_id, invoice.customer, invoice.getNature(), invoice.amount, invoice.get_payment_type_display()])
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
def invoice_create_or_edit(request, id=None, customer_id=None):
    if id:
        title = _('Edit an invoice')
        invoice = get_object_or_404(Invoice, pk=id, owner=request.user)
        customer = invoice.customer
    else:
        title = _('Draw up an invoice')
        invoice = None
        customer = get_object_or_404(Contact, pk=customer_id, owner=request.user)

    InvoiceRowFormSet = inlineformset_factory(Invoice,
                                              InvoiceRow,
                                              form=InvoiceRowForm,
                                              fk_name="invoice",
                                              extra=1)

    proposals = Proposal.objects.filter(project__customer=customer,
                                        state=PROPOSAL_STATE_ACCEPTED)

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
                invoice.save(user=user)
                invoiceForm.save_m2m()
                for invoicerowform in invoicerowformset.forms:
                    if invoicerowform.cleaned_data:
                        invoicerow = invoicerowform.save(commit=False)
                        invoicerow.invoice = invoice
                        invoicerow.save(user=user)

                        if invoicerow.balance_payments and invoice.paid_date:
                            invoicerow.proposal.state = PROPOSAL_STATE_BALANCED
                            invoicerow.proposal.save()

                for deleted_invoicerowform in invoicerowformset.deleted_forms:
                    deleted_invoicerowform.cleaned_data['ownedobject_ptr'].delete()

                messages.success(request, _('The invoice has been saved successfully'))
                return redirect(reverse('invoice_detail', kwargs={'id': invoice.id}))
            except InvoiceRowAmountError:
                transaction.rollback()
                messages.error(request, _("Amount invoiced for proposal can't be greater than proposal amount"))
            except InvoiceIdNotUniqueError:
                transaction.rollback()
                invoiceForm._errors["invoice_id"] = invoiceForm.error_class([_("Invoice id must be unique")])
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        max_invoice_id = Invoice.objects.filter(owner=request.user).aggregate(invoice_id=Max('invoice_id'))
        initial_data = None
        if not invoice:
            initial_data = {'invoice_id': (max_invoice_id['invoice_id'] or 0) + 1,
                            'edition_date': datetime.datetime.now()}
        invoiceForm = InvoiceForm(instance=invoice,
                                  prefix="invoice",
                                  initial=initial_data)
        invoicerowformset = InvoiceRowFormSet(instance=invoice)
        for invoicerowform in invoicerowformset.forms:
            invoicerowform.fields['proposal'].queryset = proposals


    return render_to_response('invoice/edit.html',
                              {'active': 'accounts',
                               'title': title,
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

    def invoice_footer(canvas, doc):
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

    filename = ugettext('invoice_%(id)d.pdf') % {'id': invoice.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    doc = BaseDocTemplate(response, title=ugettext('Invoice #%(invoice_id)d') % {'invoice_id': invoice.invoice_id}, leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    frameT = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height + 0.5 * inch, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frameT, onPage=invoice_footer), ])

    styleH = ParagraphStyle({})
    styleH.fontSize = 14
    styleH.leading = 16
    styleH.borderPadding = (5,) * 4

    styleTotal = ParagraphStyle({})
    styleTotal.fontSize = 14
    styleTotal.leading = 16
    styleTotal.borderColor = colors.black
    styleTotal.borderWidth = 0.5
    styleTotal.borderPadding = (5,) * 4

    styleH2 = ParagraphStyle({})
    styleH2.fontSize = 14
    styleH2.leading = 16


    styleTitle = ParagraphStyle({})
    styleTitle.fontSize = 14
    styleTitle.fontName = "Times-Bold"

    styleN = ParagraphStyle({})
    styleN.fontSize = 12
    styleN.leading = 14

    styleF = ParagraphStyle({})
    styleF.fontSize = 10
    styleF.alignment = TA_CENTER

    story = []

    data = []
    user_header_content = """
    %s %s<br/>
    SIRET : %s<br/>
    %s<br/>
    %s %s<br/>
    %s
    """

    customer_header_content = """
    %s<br/>
    %s<br/>
    %s<br/>
    %s %s<br/>
    %s<br/>
    """

    data.append([Paragraph(user_header_content % (user.first_name,
                                                  user.last_name,
                                                  user.get_profile().company_id,
                                                  user.get_profile().address.street.replace("\n", "<br/>"),
                                                  user.get_profile().address.zipcode,
                                                  user.get_profile().address.city,
                                                  user.get_profile().address.country or ''), styleH),
                '',
                Paragraph(customer_header_content % (invoice.customer.name,
                                                     invoice.customer.legal_form,
                                                     invoice.customer.address.street.replace("\n", "<br/>"),
                                                     invoice.customer.address.zipcode,
                                                     invoice.customer.address.city,
                                                     invoice.customer.address.country or ''), styleH)])

    t1 = Table(data, [3.5 * inch, 0.3 * inch, 3.5 * inch], [1.6 * inch])
    t1.setStyle(TableStyle([('BOX', (0, 0), (0, 0), 0.25, colors.black),
                            ('BOX', (2, 0), (2, 0), 0.25, colors.black),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

    story.append(t1)

    spacer1 = Spacer(doc.width, 0.4 * inch)
    story.append(spacer1)

    data = []
    msg = u"Dispense d'immatriculation au registre du commerce et des societes (RCS) et au repertoire des metiers (RM)"
    data.append([Paragraph(msg, styleN),
                '',
                Paragraph(_("Date : %s") % (localize(invoice.edition_date)), styleH2)])

    t2 = Table(data, [3.5 * inch, 0.3 * inch, 3.5 * inch], [0.7 * inch])
    t2.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

    story.append(t2)

    spacer2 = Spacer(doc.width, 0.4 * inch)
    story.append(spacer2)

    story.append(Paragraph(_("INVOICE #%d") % (invoice.invoice_id), styleTitle))

    spacer3 = Spacer(doc.width, 0.1 * inch)
    story.append(spacer3)

    # invoice row list
    data = [[ugettext('Label'), ugettext('Quantity'), ugettext('Unit price'), ugettext('Total')]]
    rows = invoice.invoice_rows.all()
    for row in rows:
        label = row.label
        if row.proposal.reference:
            label = label + " - [%s]" % (row.proposal.reference)
        data.append([label, localize(row.quantity), localize(row.unit_price), localize(row.quantity * row.unit_price)])

    row_count = len(rows)
    if row_count <= 16:
        max_row_count = 16
    else:
        first_page_count = 21
        normal_page_count = 33
        last_page_count = 27
        max_row_count = first_page_count + ((row_count - first_page_count) // normal_page_count * normal_page_count) + last_page_count
        if row_count - first_page_count - ((row_count - first_page_count) // normal_page_count * normal_page_count) > last_page_count:
            max_row_count = max_row_count + normal_page_count

    for i in range(max_row_count - row_count):
        data.append(['', '', '', ''])

    row_table = Table(data, [4.7 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch], (max_row_count + 1) * [0.3 * inch])
    row_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                   ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                                   ('FONT', (0, 0), (-1, 0), 'Times-Bold'),
                                   ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
                                   ('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
                                   ('BOX', (0, 1), (0, -1), 0.25, colors.black),
                                   ('BOX', (1, 1), (1, -1), 0.25, colors.black),
                                   ('BOX', (2, 1), (2, -1), 0.25, colors.black),
                                   ('BOX', (3, 1), (3, -1), 0.25, colors.black),
                                   ]))

    story.append(row_table)

    spacer4 = Spacer(doc.width, 0.55 * inch)
    story.append(spacer4)

    data = [[[Paragraph(_("Payment date : %s") % (localize(invoice.payment_date)), styleN),
              Paragraph(_("Execution dates : %(begin_date)s to %(end_date)s") % {'begin_date': localize(invoice.execution_begin_date), 'end_date' : localize(invoice.execution_end_date)}, styleN),
              Paragraph(_("Penalty begins on : %s") % (localize(invoice.penalty_date)), styleN),
              Paragraph(_("Penalty rate : %s") % (localize(invoice.penalty_rate)), styleN),
              Paragraph(_("Discount conditions : %s") % (invoice.discount_conditions), styleN)],
            '',
            [Paragraph(_("TOTAL excl. VAT : %(amount)s %(currency)s") % {'amount': localize(invoice.amount), 'currency' : "€".decode('utf-8')}, styleTotal),
             Spacer(1, 0.25 * inch),
             Paragraph(u"TVA non applicable, art. 293 B du CGI", styleN)]], ]

    footer_table = Table(data, [4.5 * inch, 0.3 * inch, 2.5 * inch], [1 * inch])
    footer_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

    story.append(footer_table)

    doc.build(story, canvasmaker=NumberedCanvas)

    return response
