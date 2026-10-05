import datetime

import jdatetime
from django import forms

from charges.models import ChargePlan, IncomeType, Payment
from config.jalali_forms import JalaliDateField, JalaliMonthField


class PaymentForm(forms.ModelForm):
    paid_at = JalaliDateField(label="تاریخ پرداخت", required=False)
    month = JalaliMonthField(label="ماه", required=False)
    charge_amount = forms.IntegerField(
        label="مبلغ شارژ (تومان)",
        required=False,
        widget=forms.NumberInput(attrs={"readonly": "readonly"}),
        help_text="با انتخاب واحد، سال و ماه خودکار پر می‌شود.",
    )

    class Meta:
        model = Payment
        fields = [
            "unit", "income_type", "year", "month",
            "paid_at", "amount", "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = jdatetime.date.today()
        self.fields["year"].initial = self.fields["year"].initial or today.year
        self.fields["month"].initial = self.fields["month"].initial or today.month
        if "paid_at" not in (self.data or {}):
            self.fields["paid_at"].initial = today.strftime("%Y/%m/%d")
        self.fields["paid_at"].help_text = "به صورت شمسی، مثل 1405/06/20"
        self.fields["unit"].label_from_instance = (
            lambda u: f"واحد {u.number} — {u.tenant_name or u.owner_name}"
        )
        self.fields["income_type"].label_from_instance = (
            lambda t: f"{t.code} — {t.title}"
        )
        self.order_fields(["unit", "income_type", "year", "month", "charge_amount", "paid_at", "amount", "description"])
        self._fill_charge_amount()

    def _selected_income_type(self):
        data = self.data or {}
        try:
            type_id = data.get("income_type") or getattr(self.instance, "income_type_id", None)
            if type_id:
                return IncomeType.objects.filter(pk=type_id).first()
        except (TypeError, ValueError):
            pass
        return getattr(self.instance, "income_type", None)

    def _is_charge(self):
        income_type = self._selected_income_type()
        return income_type.is_charge if income_type else False

    def _plan_for(self, unit, year, month):
        if not (unit and year and month):
            return None
        try:
            month = int(month)
            year = int(year)
        except (TypeError, ValueError):
            return None
        return (
            ChargePlan.objects.filter(
                unit=unit, year=year,
                start_month__lte=month, end_month__gte=month,
            ).first()
        )

    def _fill_charge_amount(self):
        unit = None
        year = None
        month = None
        if self.data:
            try:
                unit_id = self.data.get("unit")
                unit = (
                    self.fields["unit"].queryset.filter(pk=unit_id).first()
                    if unit_id else None
                )
            except (TypeError, ValueError):
                unit = None
            year = self.data.get("year")
            month = self.data.get("month")
        elif self.instance and self.instance.pk:
            unit = self.instance.unit
            year = self.instance.year
            month = self.instance.month
        plan = self._plan_for(unit, year, month)
        if plan is not None:
            self.fields["charge_amount"].initial = plan.amount
            if not self.data and (not self.instance or not self.instance.pk):
                self.fields["amount"].initial = plan.amount

    def clean(self):
        cleaned = super().clean()
        income_type = cleaned.get("income_type")
        if income_type is None:
            raise forms.ValidationError("نوع درآمد را انتخاب کنید.")
        is_charge = income_type.is_charge
        cleaned["kind"] = "charge" if is_charge else "other"
        self.instance.kind = cleaned["kind"]
        self.instance.income_type = income_type
        if is_charge and not cleaned.get("month"):
            self.add_error("month", "برای شارژ ماهیانه، ماه اجباری است.")
        if not is_charge:
            cleaned["month"] = None
            self.instance.month = None
        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)
        if obj.income_type_id:
            obj.kind = "charge" if obj.income_type.is_charge else "other"
            if obj.kind == "other":
                obj.month = None
        if commit:
            obj.save()
        return obj

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None or amount <= 0:
            raise forms.ValidationError("مبلغ پرداختی باید بیشتر از صفر باشد.")
        if not self._is_charge():
            return amount
        data = self.data or {}
        unit = None
        try:
            unit_id = data.get("unit") or getattr(self.instance, "unit_id", None)
            if unit_id:
                unit = self.fields["unit"].queryset.filter(pk=unit_id).first()
        except (TypeError, ValueError):
            unit = None
        year = data.get("year") or getattr(self.instance, "year", None)
        month = data.get("month") or getattr(self.instance, "month", None)
        plan = self._plan_for(unit, year, month)
        if plan is not None and amount > plan.amount:
            raise forms.ValidationError(
                f"مبلغ پرداختی نمی‌تواند از مبلغ شارژ ({plan.amount:,} تومان) بیشتر باشد."
            )
        return amount


class ChargePlanForm(forms.ModelForm):
    start_month = JalaliMonthField(label="ماه شروع")
    end_month = JalaliMonthField(label="ماه پایان")

    class Meta:
        model = ChargePlan
        fields = ["unit", "year", "start_month", "end_month", "amount"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = jdatetime.date.today()
        if "year" not in (self.data or {}):
            self.fields["year"].initial = today.year
        if "start_month" not in (self.data or {}):
            self.fields["start_month"].initial = today.month
        if "end_month" not in (self.data or {}):
            self.fields["end_month"].initial = today.month
        self.fields["unit"].label_from_instance = (
            lambda u: f"واحد {u.number} — {u.tenant_name or u.owner_name}"
        )


class IncomeTypeForm(forms.ModelForm):
    class Meta:
        model = IncomeType
        fields = ["title", "description", "is_charge"]
