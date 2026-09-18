from django import forms
from django.contrib.auth.models import User

from units.models import Unit


class UnitUserForm(forms.Form):
    username = forms.CharField(label="نام کاربری", max_length=150)
    password = forms.CharField(
        label="گذرواژه", max_length=128, widget=forms.PasswordInput
    )

    def __init__(self, *args, unit=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit = unit

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects.filter(username=username)
        if self.unit is not None and self.unit.user_id is not None:
            qs = qs.exclude(pk=self.unit.user_id)
        if qs.exists():
            raise forms.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = [
            "number", "owner_name", "owner_phone",
            "tenant_name", "tenant_phone",
        ]


class UnitFullForm(forms.ModelForm):
    username = forms.CharField(label="نام کاربری ورود واحد", max_length=150, required=False)
    password = forms.CharField(
        label="گذرواژه (خالی = بدون تغییر)", max_length=128,
        widget=forms.PasswordInput(render_value=False), required=False,
    )

    class Meta:
        model = Unit
        fields = [
            "number", "owner_name", "owner_phone",
            "tenant_name", "tenant_phone",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user_id:
            self.fields["username"].initial = self.instance.user.username
            self.fields["username"].required = False

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            return ""
        qs = User.objects.filter(username=username)
        if self.instance and self.instance.pk and self.instance.user_id:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError("این نام کاربری قبلاً استفاده شده است.")
        return username

    def save(self, commit=True):
        unit = super().save(commit=False)
        username = self.cleaned_data.get("username", "").strip()
        password = self.cleaned_data.get("password", "")
        if username:
            if unit.user_id is not None:
                user = unit.user
                user.username = username
                if password:
                    user.set_password(password)
                user.save()
            else:
                user = User.objects.create_user(
                    username=username, password=password or None,
                )
                if not password:
                    user.set_unusable_password()
                    user.save()
                unit.user = user
        elif commit is False:
            pass
        if commit:
            if unit.user_id is not None and unit.user.pk is None:
                unit.user.save()
            unit.save()
        return unit


class OwnershipChangeForm(forms.Form):
    name = forms.CharField(label="نام مالک جدید", max_length=100)
    phone = forms.CharField(label="موبایل مالک جدید", max_length=20)

    def __init__(self, *args, **kwargs):
        import jdatetime

        from config.jalali_forms import JalaliDateField

        super().__init__(*args, **kwargs)
        field = JalaliDateField(label="تاریخ شروع مالکیت (شمسی)")
        if not self.data:
            field.initial = jdatetime.date.today().strftime("%Y/%m/%d")
        self.fields["start_date"] = field


class TenancyChangeForm(forms.Form):
    name = forms.CharField(label="نام مستاجر جدید", max_length=100)
    phone = forms.CharField(label="موبایل مستاجر جدید", max_length=20)

    def __init__(self, *args, **kwargs):
        import jdatetime

        from config.jalali_forms import JalaliDateField

        super().__init__(*args, **kwargs)
        field = JalaliDateField(label="تاریخ شروع سکونت (شمسی)")
        if not self.data:
            field.initial = jdatetime.date.today().strftime("%Y/%m/%d")
        self.fields["start_date"] = field


class OwnershipPastForm(forms.Form):
    name = forms.CharField(label="نام مالک", max_length=100)
    phone = forms.CharField(label="موبایل مالک", max_length=20)

    def __init__(self, *args, **kwargs):
        from config.jalali_forms import JalaliDateField

        super().__init__(*args, **kwargs)
        self.fields["start_date"] = JalaliDateField(label="از تاریخ (شمسی)")
        self.fields["end_date"] = JalaliDateField(label="تا تاریخ (شمسی)", required=False)


class TenancyPastForm(forms.Form):
    name = forms.CharField(label="نام مستاجر", max_length=100)
    phone = forms.CharField(label="موبایل مستاجر", max_length=20)

    def __init__(self, *args, **kwargs):
        from config.jalali_forms import JalaliDateField

        super().__init__(*args, **kwargs)
        self.fields["start_date"] = JalaliDateField(label="از تاریخ (شمسی)")
        self.fields["end_date"] = JalaliDateField(label="تا تاریخ (شمسی)", required=False)
