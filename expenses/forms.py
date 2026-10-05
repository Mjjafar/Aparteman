import jdatetime

from config.jalali_forms import JalaliDateField
from django import forms
from expenses.models import Expense, ExpenseCategory


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["title", "requires_bill_ids"]


class ExpenseForm(forms.ModelForm):
    spent_at = JalaliDateField(label="تاریخ هزینه", required=False)

    class Meta:
        model = Expense
        fields = [
            "category", "description", "spent_at", "amount",
            "bill_id", "payment_id", "receipt",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "spent_at" not in (self.data or {}):
            self.fields["spent_at"].initial = jdatetime.date.today().strftime("%Y/%m/%d")
        self.fields["spent_at"].help_text = "به صورت شمسی، مثل 1405/06/20"
