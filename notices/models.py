from django.contrib.auth.models import User
from django.db import models

from units.models import Unit


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_digits(text):
    """Convert Latin digits to Persian digits (without thousand separators)."""
    return str(text).translate(_FA_DIGITS)


def join_fa(items):
    """Join Persian words: «الف، ب و ج»."""
    items = [str(i) for i in items if str(i)]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "، ".join(items[:-1]) + " و " + items[-1]


class Notice(models.Model):
    """اطلاعیه چاپی صورتحساب حق شارژ برای چند ماه از یک سال شمسی."""

    year = models.PositiveSmallIntegerField("سال شمسی")
    months = models.JSONField("ماه‌ها", default=list)
    work_title = models.CharField("عنوان کار", max_length=200, blank=True, default="")
    work_amount = models.PositiveIntegerField(
        "حق السهم کار (تومان)", null=True, blank=True
    )
    created_at = models.DateTimeField("تاریخ ثبت", auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notices",
        verbose_name="ثبت‌کننده",
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "اطلاعیه پرداخت"
        verbose_name_plural = "اطلاعیه‌های پرداخت"

    def month_numbers(self):
        return sorted({int(m) for m in (self.months or []) if int(m) in range(1, 13)})

    def months_display(self):
        from charges.models import JALALI_MONTHS

        return join_fa(JALALI_MONTHS[m - 1] for m in self.month_numbers())

    def period_display(self):
        return fa_digits(f"ماه‌های {self.months_display()} سال {self.year}")

    def __str__(self):
        return f"اطلاعیه {self.period_display()}"


class NoticeRow(models.Model):
    """ردیف ذخیره‌شده اطلاعیه: مبالغ هنگام ثبت قفل می‌شوند تا بازچاپ دقیق بماند."""

    notice = models.ForeignKey(
        Notice, on_delete=models.CASCADE, related_name="rows", verbose_name="اطلاعیه"
    )
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="notice_rows", verbose_name="واحد"
    )
    resident_name = models.CharField("نام ساکن", max_length=100, blank=True, default="")
    charge_amount = models.PositiveIntegerField("حق شارژ (تومان)", default=0)
    work_share = models.PositiveIntegerField("حق السهم کار (تومان)", default=0)

    class Meta:
        ordering = ["unit__number"]
        constraints = [
            models.UniqueConstraint(
                fields=["notice", "unit"], name="unique_notice_unit"
            )
        ]
        verbose_name = "ردیف اطلاعیه"
        verbose_name_plural = "ردیف‌های اطلاعیه"

    def payable_amount(self):
        return self.charge_amount + self.work_share

    def __str__(self):
        return f"{self.notice} — {self.unit}"
