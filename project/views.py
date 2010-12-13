# coding=utf-8

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _, ugettext
from django.db.transaction import commit_on_success
from django.shortcuts import get_object_or_404, redirect, render_to_response
from project.models import Project, PROJECT_STATE_STARTED, Proposal, ProposalRow, \
    Invoice, InvoiceRow, Contract, PROJECT_STATE_FINISHED, \
    PROPOSAL_STATE_BALANCED, ProposalAmountError, \
    InvoiceIdNotUniqueError, InvoiceRowAmountError
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from project.forms import ProjectForm, ProjectSearchForm, ProposalForm, \
    ProposalRowForm, InvoiceRowForm, InvoiceForm, ContractForm
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models.query_utils import Q
from django.forms.models import inlineformset_factory
from django.db.models.aggregates import Max
from contact.models import Contact
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.formats import localize
from django.db import transaction
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
def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    return render_to_response('contract/detail.html',
                              {'active': 'contact',
                               'title': '%s' % (contract),
                               'contract': contract},
                               context_instance=RequestContext(request))

@login_required
@commit_on_success
def contract_create_or_edit(request, id=None, contact_id=None):
    if id:
        title = _('Edit a contract')
        contract = get_object_or_404(Contract, pk=id, owner=request.user)
        customer = contract.customer
    else:
        title = _('Add a contract')
        contract = None
        customer = get_object_or_404(Contact, pk=contact_id, owner=request.user)

    if request.method == 'POST':
        contractForm = ContractForm(request.POST, instance=contract, prefix="contract")

        if contractForm.is_valid():
            user = request.user
            contract = contractForm.save(commit=False)
            contract.update_date = datetime.datetime.now()
            contract.customjecter = customer
            contract.save(user=user)
            contractForm.save_m2m()
            contract.to_pdf(user)

            messages.success(request, _('The contract has been saved successfully'))
            return redirect(reverse('contract_detail', kwargs={'id': contract.id}))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        contractForm = ContractForm(instance=contract, prefix="contract")

    substitution_map = Contract.get_substitution_map()
    substitution_keys = substitution_map.keys()
    keys = ''
    if len(substitution_keys):
        keys = "{{ " + " }}, {{ ".join(substitution_keys) + " }}"
    return render_to_response('contract/edit.html',
                              {'active': 'contact',
                               'title': title,
                               'contractForm': contractForm,
                               'substitution_keys': keys},
                               context_instance=RequestContext(request))

@login_required
@commit_on_success
def contract_delete(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            contract.delete()
            messages.success(request, _('The contract has been deleted successfully'))
            return redirect(reverse('project_running_list'))
        else:
            return redirect(reverse('contract_detail', kwargs={'id': contract.id}))

    return render_to_response('delete.html',
                              {'active': 'contact',
                               'title': _('Delete a contract'),
                               'object_label': 'contract "%s"' % (contract)},
                               context_instance=RequestContext(request))

@login_required
def contract_download(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    export_dir = "export/"
    filename = "contract_%s_%s.pdf" % (contract.id, contract.customer.id)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    f = open(export_dir + filename, 'r')
    response.write(f.read())
    f.close()
    return response

@login_required
def contract_get_content(request):
    contract_id = request.GET.get('id')
    contract = get_object_or_404(Contract, pk=contract_id, owner=request.user)
    data = {'title': contract.title,
            'content': contract.content}
    return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')

@login_required
def project_detail(request, id):
    project = get_object_or_404(Project, pk=id, owner=request.user)
    invoices = Invoice.objects.filter(invoice_rows__proposal__project=project)

    return render_to_response('project/detail.html',
                              {'active': 'business',
                               'title': project.name,
                               'project': project,
                               'invoices': invoices},
                               context_instance=RequestContext(request))

@login_required
@commit_on_success
def project_create_or_edit(request, id=None):
    if id:
        title = _('Edit a project')
        project = get_object_or_404(Project, pk=id, owner=request.user)
    else:
        title = _('Add a project')
        project = None

    if request.method == 'POST':
        projectForm = ProjectForm(request.POST, instance=project, prefix="project")

        if projectForm.is_valid():
            user = request.user
            project = projectForm.save(commit=False)
            project.save(user=user)
            projectForm.save_m2m()

            messages.success(request, _('The project has been saved successfully'))
            return redirect(reverse('project_detail', kwargs={'id': project.id}))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        projectForm = ProjectForm(instance=project, prefix="project")

    return render_to_response('project/edit.html',
                              {'active': 'business',
                               'title': title,
                               'projectForm': projectForm},
                               context_instance=RequestContext(request))

def project_running_list(request):
    user = request.user

    o = request.GET.get('o', 'name')
    if o not in ('name', 'customer', 'state'):
        o = 'name'
    if o == 'customer':
        order = 'customer__name'
    else:
        order = o

    ot = request.GET.get('ot', 'asc')
    if ot not in ('asc', 'desc'):
        ot = 'asc'
    if ot == 'desc':
        direction = '-'
    else:
        direction = ''

    project_list = Project.objects.filter(owner=user, state__lte=PROJECT_STATE_STARTED).distinct()
    project_list = project_list.order_by(direction + order)

    # search criteria
    form = ProjectSearchForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        project_list = project_list.filter(name__icontains=data['name'])
        if data['customer']:
            project_list = project_list.filter(Q(customer__name__icontains=data['customer']) | Q(customer__firstname__icontains=data['customer']))
        if data['state']:
            project_list = project_list.filter(state=data['state'])

    else:
        data = {'name': '',
                'customer': '',
                'state': ''}

    paginator = Paginator(project_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        projects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        projects = paginator.page(paginator.num_pages)


    return render_to_response('project/list.html',
                              {'active': 'business',
                               'title': _('Running projects'),
                               'projects': projects,
                               'o': o,
                               'ot': ot,
                               'form': form,
                               'search_criteria': data},
                               context_instance=RequestContext(request))

def project_finished_list(request):
    user = request.user

    o = request.GET.get('o', 'name')
    if o not in ('name', 'customer', 'state'):
        o = 'name'
    if o == 'customer':
        order = 'customer__name'
    else:
        order = o

    ot = request.GET.get('ot', 'asc')
    if ot not in ('asc', 'desc'):
        ot = 'asc'
    if ot == 'desc':
        direction = '-'
    else:
        direction = ''

    project_list = Project.objects.filter(owner=user, state__gte=PROJECT_STATE_FINISHED).distinct()
    project_list = project_list.order_by(direction + order)

    # search criteria
    form = ProjectSearchForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        project_list = project_list.filter(name__icontains=data['name'])
        if data['customer']:
            project_list = project_list.filter(Q(customer__name__icontains=data['customer']) | Q(customer__firstname__icontains=data['customer']))
        if data['state']:
            project_list = project_list.filter(state=data['state'])

    else:
        data = {'name': '',
                'customer': '',
                'state': ''}

    paginator = Paginator(project_list, 25)

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page request (9999) is out of range, deliver last page of results.
    try:
        projects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        projects = paginator.page(paginator.num_pages)


    return render_to_response('project/list.html',
                              {'active': 'business',
                               'title': _('Finished projects'),
                               'projects': projects,
                               'o': o,
                               'ot': ot,
                               'form': form,
                               'search_criteria': data},
                               context_instance=RequestContext(request))


@login_required
@commit_on_success
def project_delete(request, id):
    project = get_object_or_404(Project, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            project.delete()
            messages.success(request, _('The project has been deleted successfully'))
            return redirect(reverse('project_running_list'))
        else:
            return redirect(reverse('project_detail', kwargs={'id': project.id}))

    return render_to_response('delete.html',
                              {'active': 'business',
                               'title': _('Delete a project'),
                               'object_label': 'project " % s"' % (project)},
                               context_instance=RequestContext(request))


@login_required
@commit_on_success
def proposal_create_or_edit(request, id=None, project_id=None):
    if id:
        title = _('Edit a proposal')
        proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
        project = proposal.project
    else:
        title = _('Add a proposal')
        proposal = None
        project = get_object_or_404(Project, pk=project_id, owner=request.user)

    ProposalRowFormSet = inlineformset_factory(Proposal,
                                               ProposalRow,
                                               form=ProposalRowForm,
                                               fk_name="proposal",
                                               extra=1)

    if request.method == 'POST':
        proposalForm = ProposalForm(request.POST, instance=proposal, prefix="proposal")
        proposalrowformset = ProposalRowFormSet(request.POST, instance=proposal)
        if proposalForm.is_valid() and proposalrowformset.is_valid():
            try:
                user = request.user
                proposal = proposalForm.save(commit=False)
                proposal.project = project
                proposal.update_date = datetime.datetime.now()
                proposal.save(user=user)
                proposalForm.save_m2m()
                for proposalrowform in proposalrowformset.forms:
                    if proposalrowform.cleaned_data:
                        proposalrow = proposalrowform.save(commit=False)
                        proposalrow.proposal = proposal
                        proposalrow.save(user=user)

                proposal.update_amount()
                proposal.to_pdf(user)

                messages.success(request, _('The proposal has been saved successfully'))
                return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))
            except ProposalAmountError:
                proposalForm._errors["amount"] = proposalForm.error_class([_("Proposal amount can't be less sum of invoices")])
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        proposalForm = ProposalForm(instance=proposal, prefix="proposal")
        proposalrowformset = ProposalRowFormSet(instance=proposal)

    substitution_map = Contract.get_substitution_map()
    substitution_keys = substitution_map.keys()
    keys = ''
    if len(substitution_keys):
        keys = "{{ " + " }}, {{ ".join(substitution_keys) + " }}"

    return render_to_response('proposal/edit.html',
                              {'active': 'business',
                               'title': title,
                               'proposalForm': proposalForm,
                               'proposalrowformset': proposalrowformset,
                               'substitution_keys': keys},
                               context_instance=RequestContext(request))

@login_required
def proposal_detail(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
    invoices = Invoice.objects.filter(invoice_rows__proposal=proposal)
    next_states = proposal.get_next_states()

    return render_to_response('proposal/detail.html',
                              {'active': 'business',
                               'title': _('Proposal for %s') % (proposal.project),
                               'proposal': proposal,
                               'invoices': invoices,
                               'next_states': next_states},
                               context_instance=RequestContext(request))

@login_required
@commit_on_success
def proposal_delete(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            project = proposal.project
            proposal.delete()
            messages.success(request, _('The proposal has been deleted successfully'))
            return redirect(reverse('project_detail', kwargs={'id': project.id}))
        else:
            return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))

    return render_to_response('delete.html',
                              {'active': 'business',
                               'title': _('Delete a proposal'),
                               'object_label': "proposal #%d" % (proposal.id)},
                               context_instance=RequestContext(request))

@login_required
@commit_on_success
def proposal_change_state(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
    if request.method == 'POST':
        state = int(request.POST.get('next_state'))
        proposal.state = int(state)
        user = request.user
        proposal.save(user=user)

        return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))

@login_required
def proposal_download(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    export_dir = "export/"
    filename = "project_contract_%s_%s.pdf" % (proposal.id, proposal.project.customer.id)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    f = open(export_dir + filename, 'r')
    response.write(f.read())
    f.close()
    return response

@login_required
def proposal_get_contract(request):
    proposal_id = request.GET.get('id')
    proposal = get_object_or_404(Proposal, pk=proposal_id, owner=request.user)
    return HttpResponse(simplejson.dumps(proposal.contract_content), mimetype='application/javascript')

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

