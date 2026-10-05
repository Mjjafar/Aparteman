from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from units.models import Unit

JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]


class ChargePlan(models.Model):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="charge_plans",
        verbose_name="واحد",
    )
    year = models.PositiveSmallIntegerField("سال شمسی")
    start_month = models.PositiveSmallIntegerField(
        "ماه شروع",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    end_month = models.PositiveSmallIntegerField(
        "ماه پایان",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    amount = models.PositiveIntegerField("مبلغ شارژ ماهیانه (تومان)")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "year", "start_month", "end_month"],
                name="unique_plan_unit_year_months",
            )
        ]
        ordering = ["unit__number", "year", "start_month", "end_month"]
        verbose_name = "تعرفه شارژ"
        verbose_name_plural = "تعرفه‌های شارژ"

    def start_month_name(self):
        return JALALI_MONTHS[self.start_month - 1]

    def end_month_name(self):
        return JALALI_MONTHS[self.end_month - 1]

    def period_display(self):
        if self.start_month == self.end_month:
            return f"{self.start_month_name()} {self.year}"
        return f"{self.start_month_name()} تا {self.end_month_name()} {self.year}"

    def clean(self):
        super().clean()
        if (
            self.start_month is not None
            and self.end_month is not None
            and self.end_month < self.start_month
        ):
            raise ValidationError(
                {"end_month": "ماه پایان نمی‌تواند قبل از ماه شروع باشد."}
            )

    def __str__(self):
        return f"{self.unit} — {self.period_display()} — {self.amount:,} تومان"


class IncomeType(models.Model):
    code = models.CharField("کد درآمد", max_length=20, unique=True)
    title = models.CharField("عنوان درآمد", max_length=100, unique=True)
    description = models.CharField("توضیحات", max_length=255, blank=True, default="")
    is_charge = models.BooleanField(
        "شارژ ماهیانه است",
        default=False,
        help_text="فقط یک نوع درآمد می‌تواند شارژ ماهیانه باشد.",
    )

    class Meta:
        ordering = ["title"]
        verbose_name = "نوع درآمد"
        verbose_name_plural = "انواع درآمد"

    def __str__(self):
        return self.title


class Payment(models.Model):
    KIND_CHOICES = [("charge", "شارژ ماهیانه"), ("other", "درآمد متفرقه")]
    PAYER_CHOICES = [("owner", "مالک"), ("tenant", "مستاجر")]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="payments", verbose_name="واحد")
    year = models.PositiveSmallIntegerField("سال شمسی")
    month = models.PositiveSmallIntegerField(
        "ماه",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )
    payer_kind = models.CharField(
        "پرداخت‌کننده", max_length=10, choices=PAYER_CHOICES,
        blank=True, default="",
    )
    payer_name = models.CharField("نام پرداخت‌کننده", max_length=100, blank=True, default="")
    paid_at = models.DateField("تاریخ پرداخت", null=True, blank=True)
    amount = models.PositiveIntegerField("مبلغ پرداختی (تومان)")
    kind = models.CharField("نوع پرداخت", max_length=10, choices=KIND_CHOICES, default="charge")
    income_type = models.ForeignKey(
        IncomeType, on_delete=models.PROTECT, related_name="payments",
        verbose_name="نوع درآمد", null=True, blank=True,
    )
    description = models.CharField("توضیح", max_length=255, blank=True, default="")

    class Meta:
        ordering = ["income_type__code", "year", "month", "unit__number"]
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "year", "month"],
                condition=models.Q(kind="charge"),
                name="unique_charge_payment_per_unit_month",
            )
        ]

    def clean(self):
        super().clean()
        if self.kind == "charge" and self.month is None:
            raise ValidationError({"month": "برای شارژ ماهیانه، ماه اجباری است."})
        if (
            self.kind == "charge"
            and self.unit_id is not None
            and self.year is not None
            and self.month is not None
        ):
            dup = Payment.objects.filter(
                unit_id=self.unit_id, year=self.year,
                month=self.month, kind="charge",
            )
            if self.pk is not None:
                dup = dup.exclude(pk=self.pk)
            if dup.exists():
                raise ValidationError(
                    "برای این واحد در این سال و ماه قبلاً حق شارژ ثبت شده است (رکورد تکراری)."
                )

    def month_name(self):
        if not self.month:
            return "—"
        return JALALI_MONTHS[self.month - 1]

    def resident_name(self):
        if self.month:
            return self.unit.resident_at(self.year, self.month)
        return self.payer_name or self.unit.tenant_name or self.unit.owner_name

    def __str__(self):
        if self.kind == "charge" and self.month:
            return f"{self.unit} — {JALALI_MONTHS[self.month - 1]} {self.year} — {self.amount:,} تومان"
        return f"{self.unit} — متفرقه — {self.amount:,} تومان"
