# coding=utf-8

from django.utils.translation import ugettext_lazy as _, ugettext
from django.db.transaction import commit_on_success, rollback
from django.shortcuts import get_object_or_404, redirect, render_to_response
from project.models import Project, PROJECT_STATE_STARTED, Proposal, ProposalRow, \
    Contract, PROJECT_STATE_FINISHED, \
    ProposalAmountError, PROPOSAL_STATE_SENT
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
from autoentrepreneur.decorators import subscription_required
import datetime
from django.utils.encoding import smart_str
import os
from django.conf import settings

@settings_required
@subscription_required
def contract_detail(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    return render_to_response('contract/detail.html',
                              {'active': 'contact',
                               'title': '%s' % (contract),
                               'contract': contract},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
@commit_on_success
def contract_create_or_edit(request, id=None, contact_id=None):
    if id:
        title = _('Edit a master aggreement')
        contract = get_object_or_404(Contract, pk=id, owner=request.user)
        old_file = contract.contract_file
        customer = contract.customer
    else:
        title = _('Add a master aggreement')
        contract = None
        old_file = None
        customer = get_object_or_404(Contact, pk=contact_id, owner=request.user)

    contracts = Contract.objects.filter(owner=request.user).exclude(content='')
    if request.method == 'POST':
        contractForm = ContractForm(request.POST, request.FILES, instance=contract, prefix="contract")
        contractForm.fields['contract_model'].queryset = contracts

        if contractForm.is_valid():
            if request.FILES:
                try:
                    if old_file:
                        if os.path.exists(old_file.path):
                            os.remove(old_file.path)
                except:
                    pass
            user = request.user
            contract = contractForm.save(commit=False)
            contract.update_date = datetime.datetime.now()
            contract.customer = customer
            contract.save(user=user)
            contractForm.save_m2m()

            messages.success(request, _('The master aggreement has been saved successfully'))
            return redirect(reverse('contract_detail', kwargs={'id': contract.id}))
        else:
            messages.error(request, _('Data provided are invalid'))
    else:
        contractForm = ContractForm(instance=contract, prefix="contract")
        contractForm.fields['contract_model'].queryset = contracts

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
@subscription_required
@commit_on_success
def contract_delete(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    if request.method == 'POST':
        if request.POST.get('delete'):
            contract.delete()
            messages.success(request, _('The master aggreement has been deleted successfully'))
            return redirect(reverse('project_running_list'))
        else:
            return redirect(reverse('contract_detail', kwargs={'id': contract.id}))

    return render_to_response('delete.html',
                              {'active': 'contact',
                               'title': _('Delete a master aggreement'),
                               'object_label': _('the master aggreement "%(title)s"') % {'title': contract}},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
def contract_download(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    filename = ugettext('master aggreement_%(id)d.pdf') % {'id': contract.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    contract.to_pdf(request.user, response)
    return response

@settings_required
@subscription_required
def contract_uploaded_contract_download(request, id):
    contract = get_object_or_404(Contract, pk=id, owner=request.user)

    response = HttpResponse(mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment;filename="%s"'\
                                    % smart_str(contract.contract_file.name)

    response["X-Sendfile"] = "%s%s" % (settings.FILE_UPLOAD_DIR, contract.contract_file.name)
    response['Content-length'] = contract.contract_file.size
    return response

@settings_required
@subscription_required
def contract_get_content(request):
    contract_id = request.GET.get('id')
    contract = get_object_or_404(Contract, pk=contract_id, owner=request.user)
    data = {'title': contract.title,
            'content': contract.content}
    return HttpResponse(simplejson.dumps(data), mimetype='application/javascript')

@settings_required
@subscription_required
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
@subscription_required
@commit_on_success
def project_create_or_edit(request, id=None):
    if id:
        title = _('Edit a project')
        project = get_object_or_404(Project, pk=id, owner=request.user)
    else:
        title = _('Add a project')
        project = None

    contacts = Contact.objects.filter(owner=request.user)

    if request.method == 'POST':
        projectForm = ProjectForm(request.POST, instance=project, prefix="project")
        projectForm.fields['customer'].queryset = contacts

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
        projectForm.fields['customer'].queryset = contacts

    return render_to_response('project/edit.html',
                              {'active': 'business',
                               'title': title,
                               'projectForm': projectForm},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
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
@subscription_required
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
@subscription_required
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
@subscription_required
@commit_on_success
def proposal_create_or_edit(request, id=None, project_id=None):
    user = request.user
    if id:
        title = _('Edit a proposal')
        proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
        old_file = proposal.contract_file
        project = proposal.project
    else:
        title = _('Add a proposal')
        proposal = None
        old_file = None
        project = get_object_or_404(Project, pk=project_id, owner=request.user)

    ProposalRowFormSet = inlineformset_factory(Proposal,
                                               ProposalRow,
                                               form=ProposalRowForm,
                                               fk_name="proposal",
                                               extra=1)

    proposals = Proposal.objects.filter(owner=request.user).exclude(contract_content='')

    if request.method == 'POST':
        proposalForm = ProposalForm(request.POST, request.FILES, instance=proposal, prefix="proposal")
        proposalForm.fields['contract_model'].queryset = proposals
        proposalrowformset = ProposalRowFormSet(request.POST, instance=proposal)
        if proposalForm.is_valid() and proposalrowformset.is_valid():
            if request.FILES:
                try:
                    if old_file:
                        if os.path.exists(old_file.path):
                            os.remove(old_file.path)
                except:
                    pass
            try:
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
                if proposal.begin_date and proposal.end_date and proposal.begin_date > proposal.end_date:
                    messages.warning(request, _("Begin date is greater than end date, is this normal ?"))
                if proposal.expiration_date and proposal.expiration_date < datetime.date.today() and proposal.state < PROPOSAL_STATE_SENT:
                    messages.warning(request, _("Expiration date is in the past while the proposal is not yet sent, is this normal ?"))
                return redirect(reverse('proposal_detail', kwargs={'id': proposal.id}))
            except ProposalAmountError:
                rollback()
                messages.error(request, _("Proposal amount can't be less than sum of invoices"))
        else:
            import pdb;pdb.set_trace()
            messages.error(request, _('Data provided are invalid'))
    else:
        proposalForm = ProposalForm(instance=proposal, prefix="proposal")
        proposalForm.fields['contract_model'].queryset = proposals
        proposalrowformset = ProposalRowFormSet(instance=proposal)

    substitution_map = Proposal.get_substitution_map()
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
@subscription_required
def proposal_detail(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)
    invoices = Invoice.objects.filter(invoice_rows__proposal=proposal).distinct()
    next_states = proposal.get_next_states()
    template = 'proposal/detail.html'
    if request.GET.get('ajax', False):
        template = 'proposal/detail_ajax.html'
    return render_to_response(template,
                              {'active': 'business',
                               'title': _('Proposal for %s') % (proposal.project),
                               'proposal': proposal,
                               'invoices': invoices,
                               'next_states': next_states},
                               context_instance=RequestContext(request))

@settings_required
@subscription_required
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
@subscription_required
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
@subscription_required
def proposal_download(request, id):
    user = request.user
    proposal = get_object_or_404(Proposal, pk=id, owner=user)

    response = HttpResponse(mimetype='application/pdf')
    proposal.to_pdf(user, response)
    return response

@settings_required
@subscription_required
def proposal_contract_download(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    filename = ugettext('proposal_contract_%(id)d.pdf') % {'id': proposal.id}
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % (filename)

    proposal.contract_to_pdf(request.user, response)
    return response

@settings_required
@subscription_required
def proposal_uploaded_contract_download(request, id):
    proposal = get_object_or_404(Proposal, pk=id, owner=request.user)

    response = HttpResponse(mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment;filename="%s"'\
                                    % smart_str(proposal.contract_file.name)
    response["X-Sendfile"] = settings.FILE_UPLOAD_DIR + proposal.contract_file.name
    response['Content-length'] = proposal.contract_file.size
    return response

@settings_required
@subscription_required
def proposal_get_contract(request):
    proposal_id = request.GET.get('id')
    proposal = get_object_or_404(Proposal, pk=proposal_id, owner=request.user)
    return HttpResponse(simplejson.dumps(proposal.contract_content), mimetype='application/javascript')

