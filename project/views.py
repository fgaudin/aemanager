# coding=utf-8

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _, ugettext
from django.db.transaction import commit_on_success
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
import datetime

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

    export_dir = "export/"
    filename = "contract_%s_%s.pdf" % (contract.id, contract.customer.id)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    f = open(export_dir + filename, 'r')
    response.write(f.read())
    f.close()
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

@settings_required
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
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    export_dir = "export/"
    filename = "project_contract_%s_%s.pdf" % (proposal.id, proposal.project.customer.id)

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    f = open(export_dir + filename, 'r')
    response.write(f.read())
    f.close()
    return response

@settings_required
def proposal_get_contract(request):
    proposal_id = request.GET.get('id')
    proposal = get_object_or_404(Proposal, pk=proposal_id, owner=request.user)
    return HttpResponse(simplejson.dumps(proposal.contract_content), mimetype='application/javascript')

