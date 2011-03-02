from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from project.models import Project, PROJECT_STATE, PROJECT_STATE_STARTED, \
    Proposal, ProposalRow, Contract
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
        exclude = ['owner', 'project', 'update_date', 'amount']

    def __init__(self, *args, **kwargs):
        super(ProposalForm, self).__init__(*args, **kwargs)
        self.fields['begin_date'].widget.attrs['class'] = 'date'
        self.fields['end_date'].widget.attrs['class'] = 'date'
        self.fields['expiration_date'].widget.attrs['class'] = 'date'

class ProposalRowForm(ModelForm):
    quantity = forms.DecimalField(max_digits=5, decimal_places=1, label=_('Quantity'), localize=True)
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Unit price'), localize=True)

    class Meta:
        model = ProposalRow
        exclude = ['owner']

    def __init__(self, *args, **kwargs):
        super(ProposalRowForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['class'] = 'quantity-field'
        self.fields['unit_price'].widget.attrs['class'] = 'unit-price-field'
