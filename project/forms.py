from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from project.models import Project, PROJECT_STATE, PROJECT_STATE_STARTED, \
    Proposal, ProposalRow, Invoice, InvoiceRow, Contract
from django import forms

class ContractForm(ModelForm):
    contract_model = forms.ModelChoiceField(label=_('Model'),
                                            required=False,
                                            queryset=Contract.objects.exclude(content=''))


    class Meta:
        model = Contract
        exclude = ['owner', 'update_date', 'customer']

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ['owner']

PROJECT_STATE_SEARCH = (('', '-------------'),) + PROJECT_STATE[:PROJECT_STATE_STARTED]

class ProjectSearchForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=False)
    customer = forms.CharField(label=_('Customer'), required=False)
    state = forms.ChoiceField(label=_('State'), required=False, choices=PROJECT_STATE_SEARCH)

class ProposalForm(ModelForm):
    contract_model = forms.ModelChoiceField(label=_('Model'),
                                            required=False,
                                            queryset=Proposal.objects.exclude(contract_content=''))

    class Meta:
        model = Proposal
        exclude = ['owner', 'project', 'update_date']

class ProposalRowForm(ModelForm):
    class Meta:
        model = ProposalRow
        exclude = ['owner']

class InvoiceForm(ModelForm):
    class Meta:
        model = Invoice
        exclude = ['owner', 'proposal']

class InvoiceRowForm(ModelForm):
    class Meta:
        model = InvoiceRow
        exclude = ['owner']
