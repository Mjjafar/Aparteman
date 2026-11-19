from django import forms

from config.jalali_forms import JALALI_MONTH_CHOICES


class NoticeForm(forms.Form):
    year = forms.IntegerField(
        label="سال شمسی",
        min_value=1300,
        max_value=1499,
        error_messages={
            "required": "سال شمسی را وارد کنید.",
            "invalid": "سال شمسی معتبر نیست (مثل ۱۴۰۵).",
        },
    )
    months = forms.TypedMultipleChoiceField(
        label="ماه‌ها",
        choices=JALALI_MONTH_CHOICES,
        coerce=int,
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "حداقل یک ماه را انتخاب کنید."},
    )
    work_title = forms.CharField(
        label="عنوان کار (اختیاری)",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "مثل تعمیر آسانسور"}),
    )
    work_amount = forms.IntegerField(
        label="حق السهم بابت کار — هر واحد (تومان، اختیاری)",
        min_value=0,
        required=False,
    )
