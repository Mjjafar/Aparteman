from django.core.exceptions import ValidationError
from django.db import models


class ExpenseCategory(models.Model):
    title = models.CharField("عنوان", max_length=100, unique=True)
    requires_bill_ids = models.BooleanField(
        "شناسه قبض/پرداخت اجباری است",
        default=False,
        help_text="برای دسته‌های قبض (آب، گاز، برق) فعال کنید.",
    )

    class Meta:
        ordering = ["title"]
        verbose_name = "نوع مخارج"
        verbose_name_plural = "انواع مخارج"

    def __str__(self):
        return self.title


class Expense(models.Model):
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT,
        related_name="expenses", verbose_name="نوع مخارج",
    )
    spent_at = models.DateField("تاریخ هزینه")
    amount = models.PositiveIntegerField("مبلغ (تومان)")
    bill_id = models.CharField("شناسه قبض", max_length=100, blank=True, default="")
    payment_id = models.CharField("شناسه پرداخت", max_length=100, blank=True, default="")
    description = models.CharField("شرح", max_length=255)
    receipt = models.FileField("فاکتور", upload_to="receipts/%Y/%m/", null=True, blank=True)

    class Meta:
        ordering = ["-spent_at"]
        verbose_name = "هزینه"
        verbose_name_plural = "مخارج"

    def clean(self):
        super().clean()
        if self.category_id is not None and self.category.requires_bill_ids:
            missing = []
            if not self.bill_id:
                missing.append("شناسه قبض")
            if not self.payment_id:
                missing.append("شناسه پرداخت")
            if missing:
                raise ValidationError(
                    "برای دسته‌های قبض، شناسه قبض و شناسه پرداخت اجباری است."
                )

    def __str__(self):
        return f"{self.category} — {self.amount:,} تومان"
