from django.forms import ModelForm
from accounts.models import Expense, Invoice, InvoiceRow, INVOICE_STATE_PAID
from django import forms
from django.utils.translation import ugettext_lazy as _

class ExpenseForm(ModelForm):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Amount'), localize=True)

    class Meta:
        model = Expense
        exclude = ['owner']

class InvoiceForm(ModelForm):
    penalty_rate = forms.DecimalField(max_digits=4, decimal_places=2, label=_('Penalty rate'), localize=True, required=False)

    class Meta:
        model = Invoice
        exclude = ['owner', 'proposal', 'amount']

    def clean(self):
        super(InvoiceForm, self).clean()
        cleaned_data = self.cleaned_data
        state = cleaned_data.get("state")
        paid_date = cleaned_data.get("paid_date")

        if state == INVOICE_STATE_PAID and not paid_date:
            msg = _('This field is required since invoice state is set to "paid".')
            self._errors["paid_date"] = self.error_class([msg])

            del cleaned_data["paid_date"]

        return cleaned_data

class InvoiceRowForm(ModelForm):
    quantity = forms.DecimalField(max_digits=5, decimal_places=1, label=_('Quantity'), localize=True)
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Unit price'), localize=True)

    class Meta:
        model = InvoiceRow
        exclude = ['owner']

    def __init__(self, *args, **kwargs):
        super(InvoiceRowForm, self).__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['class'] = 'quantity-field'
        self.fields['unit_price'].widget.attrs['class'] = 'unit-price-field'
