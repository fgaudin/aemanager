# coding=utf-8

from django.utils.translation import ugettext_lazy as _, ugettext
from django.db.transaction import commit_on_success, rollback
from django.shortcuts import get_object_or_404, redirect, render_to_response
from project.models import Project, PROJECT_STATE_STARTED, Proposal, ProposalRow, \
    Contract, PROJECT_STATE_FINISHED, \
    ProposalAmountError
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from project.forms import ProjectForm, ProjectSearchForm, ProposalForm, \
    ProposalRowForm, ContractForm
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models.query_utils import Q
from django.forms.models import inlineformset_factory
from contact.models import Contact
from django.http import HttpResponse
from django.utils import simplejson
from accounts.models import Invoice
from core.decorators import settings_required
from django.utils.formats import localize
from custom_canvas import NumberedCanvas
import datetime
from reportlab.platypus import Paragraph, Frame, Spacer, BaseDocTemplate, PageTemplate
from reportlab.lib.styles import ParagraphStyle
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

@settings_required
def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    return render_to_response('contract/detail.html',
                              {'active': 'contact',
                               'title': '%s' % (contract),
                               'contract': contract},
                               context_instance=RequestContext(request))

@settings_required
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
            contract.customer = customer
            contract.save(user=user)
            contractForm.save_m2m()

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

@settings_required
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

@settings_required
def contract_download(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    filename = ugettext('contract_%(id)d.pdf') % {'id': contract.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    contract.to_pdf(request.user, response)
    return response

@settings_required
def contract_get_content(request):
    contract_id = request.GET.get('id')
    contract = get_object_or_404(Contract, pk=contract_id, owner=request.user)
    data = {'title': contract.title,
            'content': contract.content}
    return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')

@settings_required
def project_detail(request, id):
    project = get_object_or_404(Project, pk=id, owner=request.user)
    invoices = Invoice.objects.filter(invoice_rows__proposal__project=project).distinct()

    return render_to_response('project/detail.html',
                              {'active': 'business',
                               'title': project.name,
                               'project': project,
                               'invoices': invoices},
                               context_instance=RequestContext(request))

@settings_required
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

@settings_required
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

@settings_required
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


@settings_required
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


@settings_required
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

                for deleted_proposalrowform in proposalrowformset.deleted_forms:
                    deleted_proposalrowform.cleaned_data['ownedobject_ptr'].delete()

                proposal.update_amount()

                messages.success(request, _('The proposal has been saved successfully'))
                return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))
            except ProposalAmountError:
                rollback()
                messages.error(request, _("Proposal amount can't be less than sum of invoices"))
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

@settings_required
def proposal_detail(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
    invoices = Invoice.objects.filter(invoice_rows__proposal=proposal).distinct()
    next_states = proposal.get_next_states()

    return render_to_response('proposal/detail.html',
                              {'active': 'business',
                               'title': _('Proposal for %s') % (proposal.project),
                               'proposal': proposal,
                               'invoices': invoices,
                               'next_states': next_states},
                               context_instance=RequestContext(request))

@settings_required
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

@settings_required
@commit_on_success
def proposal_change_state(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
    if request.method == 'POST':
        state = int(request.POST.get('next_state'))
        proposal.state = int(state)
        user = request.user
        proposal.save(user=user)

        return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))

@settings_required
def proposal_download(request, id):
    user = request.user
    proposal = get_object_or_404(Proposal, pk=id, owner=user)

    def proposal_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Times-Roman', 10)
        PAGE_WIDTH = defaultPageSize[0]
        canvas.drawCentredString(PAGE_WIDTH / 2.0, 0.5 * inch, "%s %s - SIRET : %s - %s, %s %s, %s" % (user.first_name,
                                                                                     user.last_name,
                                                                                     user.get_profile().company_id,
                                                                                     user.get_profile().address.street,
                                                                                     user.get_profile().address.zipcode,
                                                                                     user.get_profile().address.city,
                                                                                     user.get_profile().address.country.country_name))
        canvas.restoreState()

    filename = ugettext('proposal_%(id)d.pdf') % {'id': proposal.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    doc = BaseDocTemplate(response, title=ugettext('Proposal %(reference)s') % {'reference': proposal.reference}, leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    frameT = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height + 0.5 * inch, id='normal')
    doc.addPageTemplates([PageTemplate(id='all', frames=frameT, onPage=proposal_footer), ])

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
                                                  user.get_profile().address.country.country_name), styleH),
                '',
                Paragraph(customer_header_content % (proposal.project.customer.name,
                                                     proposal.project.customer.legal_form,
                                                     proposal.project.customer.address.street.replace("\n", "<br/>"),
                                                     proposal.project.customer.address.zipcode,
                                                     proposal.project.customer.address.city,
                                                     proposal.project.customer.address.country.country_name), styleH)])

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
                Paragraph(_("Date : %s") % (localize(proposal.update_date)), styleH2)])

    t2 = Table(data, [3.5 * inch, 0.3 * inch, 3.5 * inch], [0.7 * inch])
    t2.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

    story.append(t2)

    spacer2 = Spacer(doc.width, 0.4 * inch)
    story.append(spacer2)

    story.append(Paragraph(_("PROPOSAL %s") % (proposal.reference), styleTitle))

    spacer3 = Spacer(doc.width, 0.1 * inch)
    story.append(spacer3)

    # invoice row list
    data = [[ugettext('Label'), ugettext('Quantity'), ugettext('Unit price'), ugettext('Total')]]
    rows = proposal.proposal_rows.all()
    for row in rows:
        label = row.label
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

    data = [[[Paragraph(_("Proposal valid through : %s") % (localize(proposal.expiration_date)), styleN),
              Paragraph(_("Execution dates : %(begin_date)s to %(end_date)s") % {'begin_date': localize(proposal.begin_date), 'end_date' : localize(proposal.end_date)}, styleN)],
            '',
            [Paragraph(_("TOTAL excl. VAT : %(amount)s %(currency)s") % {'amount': localize(proposal.amount), 'currency' : "€".decode('utf-8')}, styleTotal),
             Spacer(1, 0.25 * inch),
             Paragraph(u"TVA non applicable, art. 293 B du CGI", styleN)]], ]

    footer_table = Table(data, [4.5 * inch, 0.3 * inch, 2.5 * inch], [1 * inch])
    footer_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ]))

    story.append(footer_table)

    doc.build(story, canvasmaker=NumberedCanvas)

    return response

@settings_required
def proposal_contract_download(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    filename = ugettext('proposal_contract_%(id)d.pdf') % {'id': proposal.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    proposal.to_pdf(request.user, response)
    return response

@settings_required
def proposal_get_contract(request):
    proposal_id = request.GET.get('id')
    proposal = get_object_or_404(Proposal, pk=proposal_id, owner=request.user)
    return HttpResponse(simplejson.dumps(proposal.contract_content), mimetype='application/javascript')

