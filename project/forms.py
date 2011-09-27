from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from project.models import Project, PROJECT_STATE, PROJECT_STATE_STARTED, \
    Proposal, ProposalRow, Contract, PAYMENT_DELAY_OTHER, \
    PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH, \
    PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH_PLUS_DELAY
from django import forms

class ContractForm(ModelForm):
    contract_model = forms.ModelChoiceField(label=_('Model'),
                                            required=False,
                                            queryset=Contract.objects.exclude(content=''))


    class Meta:
        model = Contract
        exclude = ['owner', 'uuid', 'update_date', 'customer']

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        exclude = ['owner', 'uuid']

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
        exclude = ['owner', 'uuid', 'project', 'update_date', 'amount']

    def __init__(self, *args, **kwargs):
        super(ProposalForm, self).__init__(*args, **kwargs)
        self.fields['begin_date'].widget.attrs['class'] = 'date'
        self.fields['end_date'].widget.attrs['class'] = 'date'
        self.fields['expiration_date'].widget.attrs['class'] = 'date'

    def clean(self):
        super(ProposalForm, self).clean()
        cleaned_data = self.cleaned_data
        if cleaned_data['payment_delay'] == PAYMENT_DELAY_OTHER:
            days = cleaned_data['payment_delay_other']
            if not days:
                msg = _("Delay is missing. If you choose \"other\", you have to enter your own value.")
                self._errors["payment_delay"] = self.error_class([msg])
            else:
                type = cleaned_data['payment_delay_type_other']
                if not type:
                    msg = _("Delay type is missing. If you choose \"other\", you have to select the type of delay to use.")
                    self._errors["payment_delay"] = self.error_class([msg])
                elif type in [PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH,
                            PAYMENT_DELAY_TYPE_OTHER_END_OF_MONTH_PLUS_DELAY]:
                    if days > 45:
                        msg = _("Payment delay can't exceed 45 days end of month.")
                        self._errors["payment_delay"] = self.error_class([msg])
                else:
                    if days > 60:
                        msg = _("Payment delay can't exceed 60 days.")
                        self._errors["payment_delay"] = self.error_class([msg])
        return cleaned_data

class ProposalRowForm(ModelForm):
    quantity = forms.DecimalField(max_digits=5, decimal_places=1, label=_('Quantity'), localize=True)
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Unit price'), localize=True)

    class Meta:
        model = ProposalRow
        exclude = ['owner', 'uuid']

    def __init__(self, *args, **kwargs):
        super(ProposalRowForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['class'] = 'quantity-field'
        self.fields['unit_price'].widget.attrs['class'] = 'unit-price-field'
        self.fields['detail'].widget.attrs['class'] = 'row-detail'
