from django.forms import ModelForm
from accounts.models import Expense
from django import forms
from django.utils.translation import ugettext_lazy as _

class ExpenseForm(ModelForm):
    amount = forms.DecimalField(max_digits=12, decimal_places=2, label=_('Amount'), localize=True)

    class Meta:
        model = Expense
        exclude = ['owner']
