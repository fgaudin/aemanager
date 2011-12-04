from django.forms import ModelForm
from accounts.models import Expense, Invoice, InvoiceRow, INVOICE_STATE_PAID, \
    MAX_INVOICE_ID
from django import forms
from django.utils.translation import ugettext_lazy as _

class ExpenseForm(ModelForm):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Amount'), localize=True)

    class Meta:
        model = Expense
        exclude = ['owner', 'uuid']

    def __init__(self, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['class'] = 'date'

class InvoiceForm(ModelForm):
    invoice_id = forms.IntegerField(max_value=MAX_INVOICE_ID,
                                    label=_('Invoice id'),
                                    help_text=_('An integer less than or equal to %d. Must be sequential.') % (MAX_INVOICE_ID))
    penalty_rate = forms.DecimalField(max_digits=4,
                                      decimal_places=2,
                                      label=_('Penalty rate'),
                                      localize=True,
                                      required=False,
                                      help_text=_('at least three times the <a href="%(french_rate)s">legal rate</a> or by default <a href="%(ecb_rate)s">rate applied by the European Central Bank</a> to its most recent refinancing operation plus 10 points') % {'french_rate': 'http://www.minefe.gouv.fr/directions_services/dgtpe/taux/taux_legal.php',
                                                                                                                                                                                                                                                                              'ecb_rate': 'http://fr.global-rates.com/taux-de-interets/banques-centrales/banque-centrale-europeenne/taux-de-bce.aspx'})

    class Meta:
        model = Invoice
        exclude = ['owner', 'uuid', 'proposal', 'amount']

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.fields['edition_date'].widget.attrs['class'] = 'date'
        self.fields['payment_date'].widget.attrs['class'] = 'date'
        self.fields['paid_date'].widget.attrs['class'] = 'date'
        self.fields['execution_begin_date'].widget.attrs['class'] = 'date'
        self.fields['execution_end_date'].widget.attrs['class'] = 'date'
        self.fields['penalty_date'].widget.attrs['class'] = 'date'
        self.fields['footer_note'].widget.attrs['size'] = '90'

    def clean(self):
        super(InvoiceForm, self).clean()
        cleaned_data = self.cleaned_data
        state = cleaned_data.get("state")
        paid_date = cleaned_data.get("paid_date")

        if state == INVOICE_STATE_PAID and not paid_date:
            msg = _('This field is required since invoice state is set to "paid".')
            self._errors["paid_date"] = self.error_class([msg])

            del cleaned_data["paid_date"]

        payment_type = cleaned_data.get('payment_type')
        if state == INVOICE_STATE_PAID and not payment_type:
            msg = _('This field is required since invoice state is set to "paid".')
            self._errors["payment_type"] = self.error_class([msg])

            del cleaned_data["payment_type"]

        return cleaned_data

class InvoiceRowForm(ModelForm):
    quantity = forms.DecimalField(max_digits=5, decimal_places=1, label=_('Quantity'), localize=True)
    unit_price = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Unit price'), localize=True)

    class Meta:
        model = InvoiceRow
        exclude = ['owner', 'uuid']

    def __init__(self, *args, **kwargs):
        super(InvoiceRowForm, self).__init__(*args, **kwargs)
        self.fields['label'].widget.attrs['class'] = 'label-field'
        self.fields['proposal'].widget.attrs['class'] = 'proposal-field'
        self.fields['balance_payments'].widget.attrs['class'] = 'balance-payments-field'
        self.fields['category'].widget.attrs['class'] = 'category-field'
        self.fields['quantity'].widget.attrs['class'] = 'quantity-field'
        self.fields['unit_price'].widget.attrs['class'] = 'unit-price-field'
        self.fields['vat_rate'].widget.attrs['class'] = 'vat-rate-field'
        self.fields['detail'].widget.attrs['class'] = 'row-detail'
