# coding=utf-8

from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext
from accounts.forms import ExpenseForm, InvoiceRowForm, InvoiceForm
from accounts.models import Expense, Invoice, InvoiceRow, InvoiceRowAmountError, \
    InvoiceIdNotUniqueError
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.formats import localize
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit_on_success
from contact.models import Contact
from django.forms.models import inlineformset_factory
from project.models import Proposal, PROPOSAL_STATE_BALANCED
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.aggregates import Max
import datetime
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Frame, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

@login_required
def expense_list(request):
    user = request.user
    expenses = Expense.objects.filter(owner=user).order_by('-date')
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

@login_required
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

@login_required
@commit_on_success
def expense_edit(request):
    id = request.GET.get('id')
    expense = get_object_or_404(Expense, pk=id)
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

@login_required
@commit_on_success
def expense_delete(request):
    response = {'error': 'ko'}
    if request.POST:
        id = int(request.POST.get('id'))
        if id:
            Expense.objects.filter(pk=id).delete()
            response['error'] = 'ok'
            response['id'] = id

    return HttpResponse(simplejson.dumps(response),
                        mimetype='application/javascript')

@login_required
def invoice_list(request):
    user = request.user
    invoices = Invoice.objects.filter(owner=user).order_by('-invoice_id')
    return render_to_response('invoice/list.html',
                              {'active': 'accounts',
                               'title': _('Invoices'),
                               'invoices': invoices},
                              context_instance=RequestContext(request))


@login_required
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

    proposals = Proposal.objects.filter(project__customer=customer)

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
                              {'active': 'business',
                               'title': title,
                               'invoiceForm': invoiceForm,
                               'invoicerowformset': invoicerowformset},
                               context_instance=RequestContext(request))

@login_required
def invoice_detail(request, id):
    invoice = get_object_or_404(Invoice, pk=id, owner=request.user)

    return render_to_response('invoice/detail.html',
                              {'active': 'business',
                               'title': _('Invoice for %s') % (invoice.customer),
                               'invoice': invoice},
                               context_instance=RequestContext(request))

@login_required
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
                              {'active': 'business',
                               'title': _('Delete an invoice'),
                               'object_label': "invoice #%d" % (invoice.id)},
                               context_instance=RequestContext(request))

@login_required
def invoice_download(request, id):
    invoice = get_object_or_404(Invoice, pk=id, owner=request.user)
    filename = "invoice_%s.pdf" % (invoice.invoice_id)
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)
    user = request.user

    # drawing content
    WIDTH = defaultPageSize[0]
    HEIGHT = defaultPageSize[1]
    c = Canvas(response)
    styleH = ParagraphStyle({})
    styleH.fontSize = 14
    styleH.leading = 16
    styleH.borderColor = colors.black
    styleH.borderWidth = 0.5
    styleH.borderPadding = (5,) * 4

    styleH2 = ParagraphStyle({})
    styleH2.fontSize = 14
    styleH2.leading = 16


    styleTitle = ParagraphStyle({})
    styleTitle.fontSize = 14
    styleTitle.leading = 16
    styleTitle.fontName = "Times-Bold"

    styleN = ParagraphStyle({})
    styleN.fontSize = 12
    styleN.leading = 14

    styleF = ParagraphStyle({})
    styleF.fontSize = 10
    styleF.alignment = TA_CENTER

    showBoundary = 0

    # draw header
    # draw user header
    user_header = Frame(0.5 * inch, HEIGHT - 2.5 * inch, 3.5 * inch, 2 * inch, showBoundary=showBoundary)
    story = []
    user_header_content = """
    %s %s<br/>
    SIRET : %s<br/>
    %s<br/>
    %s %s<br/>
    %s
    """
    story.append(Paragraph(user_header_content % (user.first_name,
                                                  user.last_name,
                                                  user.get_profile().company_id,
                                                  user.get_profile().address.street.replace("\n", "<br/>"),
                                                  user.get_profile().address.zipcode,
                                                  user.get_profile().address.city,
                                                  user.get_profile().address.country.country_name),
                           styleH))
    user_header.addFromList(story, c)

    # draw customer header
    story = []
    customer_header = Frame(WIDTH - 4 * inch, HEIGHT - 2.5 * inch, 3.5 * inch, 2 * inch, showBoundary=showBoundary)
    customer_header_content = """
    %s<br/>
    %s<br/>
    %s<br/>
    %s %s<br/>
    %s<br/>
    """
    story.append(Paragraph(customer_header_content % (invoice.customer.name,
                                                      invoice.customer.legal_form,
                                                      invoice.customer.address.street.replace("\n", "<br/>"),
                                                      invoice.customer.address.zipcode,
                                                      invoice.customer.address.city,
                                                      invoice.customer.address.country.country_name),
                           styleH))
    customer_header.addFromList(story, c)

    # draw general header
    story = []
    general_header_left = Frame(0.5 * inch, HEIGHT - 3.6 * inch, 3.5 * inch, 1 * inch, showBoundary=showBoundary)
    msg = u"Dispense d'immatriculation au registre du commerce et des societes (RCS) et au repertoire des metiers (RM)"
    story.append(Paragraph(msg, styleN))
    general_header_left.addFromList(story, c)

    story = []
    general_header_right = Frame(WIDTH - 4 * inch, HEIGHT - 3.6 * inch, 3.5 * inch, 1 * inch, showBoundary=showBoundary)
    story.append(Paragraph(_("Date : %s") % (localize(invoice.edition_date)), styleH2))
    general_header_right.addFromList(story, c)

    # main frame
    story = []
    main_frame = Frame(0.5 * inch, 2.25 * inch, WIDTH - 1 * inch, 5.75 * inch, showBoundary=showBoundary)
    story.append(Paragraph(_("INVOICE #%d") % (invoice.invoice_id), styleTitle))
    main_frame.addFromList(story, c)

    # draw invoice rows
    data = [[ugettext('Label'), ugettext('Quantity'), ugettext('Unit price'), ugettext('Total')]]
    rows = invoice.invoice_rows.all()
    for row in rows:
        label = row.label
        if row.proposal.reference:
            label = label + " - [%s]" % (row.proposal.reference)
        data.append([label, row.quantity, row.unit_price, row.quantity * row.unit_price])

    max_row_count = 16

    for i in range(max_row_count - len(rows)):
        data.append(['', '', '', ''])

    t = Table(data, [4.7 * inch, 0.8 * inch, 0.9 * inch, 0.8 * inch], (max_row_count + 1) * [0.3 * inch])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                           ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                           ('FONT', (0, 0), (-1, 0), 'Times-Bold'),
                           ('BOX', (0, 0), (-1, 0), 0.25, colors.black),
                           ('INNERGRID', (0, 0), (-1, 0), 0.25, colors.black),
                           ('BOX', (0, 1), (0, -1), 0.25, colors.black),
                           ('BOX', (1, 1), (1, -1), 0.25, colors.black),
                           ('BOX', (2, 1), (2, -1), 0.25, colors.black),
                           ('BOX', (3, 1), (3, -1), 0.25, colors.black),
                           ]))

    story = []
    story.append(t)
    main_frame.addFromList(story, c)

    # draw amount and information
    bottom_left_frame = Frame(0.5 * inch, 0.75 * inch, 4.5 * inch, 1.25 * inch, showBoundary=showBoundary)
    story = []
    story.append(Paragraph(_("Payment date : %s") % (localize(invoice.payment_date)), styleN))
    story.append(Paragraph(_("Execution dates : %(begin_date)s to %(end_date)s") % {'begin_date': localize(invoice.execution_begin_date), 'end_date' : localize(invoice.execution_end_date)}, styleN))
    story.append(Paragraph(_("Penalty begins on : %s") % (localize(invoice.penalty_date)), styleN))
    story.append(Paragraph(_("Penalty rate : %s") % (localize(invoice.penalty_rate)), styleN))
    story.append(Paragraph(_("Discount conditions : %s") % (invoice.discount_conditions), styleN))
    bottom_left_frame.addFromList(story, c)

    bottom_right_frame = Frame(WIDTH - 3 * inch, 0.75 * inch, 2.5 * inch, 1.25 * inch, showBoundary=showBoundary)
    story = []
    story.append(Paragraph(_("TOTAL : %(amount)s %(currency)s") % {'amount': localize(invoice.amount), 'currency' : "€".decode('utf-8')}, styleH))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(u"TVA non applicable, art. 293 B du CGI", styleN))
    bottom_right_frame.addFromList(story, c)

    # draw footer
    story = []
    footer = Frame(0.5 * inch, 0.2 * inch, WIDTH - 1 * inch, 0.37 * inch, showBoundary=showBoundary)
    story.append(Paragraph("%s %s - SIRET : %s - %s, %s %s, %s" % (user.first_name,
                                                           user.last_name,
                                                           user.get_profile().company_id,
                                                           user.get_profile().address.street,
                                                           user.get_profile().address.zipcode,
                                                           user.get_profile().address.city,
                                                           user.get_profile().address.country.country_name),
                           styleF))

    footer.addFromList(story, c)

    c.save()

    return response

