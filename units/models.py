from django.contrib.auth.models import User
from django.db import models


class Unit(models.Model):
    number = models.PositiveSmallIntegerField("شماره واحد", unique=True)
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="کاربر ورود",
    )
    owner_name = models.CharField("نام مالک", max_length=100)
    owner_phone = models.CharField("موبایل مالک", max_length=20)
    tenant_name = models.CharField("نام مستاجر", max_length=100, blank=True, default="")
    tenant_phone = models.CharField("موبایل مستاجر", max_length=20, blank=True, default="")

    class Meta:
        ordering = ["number"]
        verbose_name = "واحد"
        verbose_name_plural = "واحدها"

    def __str__(self):
        return f"واحد {self.number}"


class OwnershipHistory(models.Model):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="ownerships", verbose_name="واحد"
    )
    name = models.CharField("نام مالک", max_length=100)
    phone = models.CharField("موبایل مالک", max_length=20)
    start_date = models.DateField("از تاریخ")
    end_date = models.DateField("تا تاریخ", null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "سابقه مالکیت"
        verbose_name_plural = "سوابق مالکیت"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class TenancyHistory(models.Model):
    unit = models.ForeignKey(
        Unit, on_delete=models.CASCADE, related_name="tenancies", verbose_name="واحد"
    )
    name = models.CharField("نام مستاجر", max_length=100)
    phone = models.CharField("موبایل مستاجر", max_length=20)
    start_date = models.DateField("از تاریخ")
    end_date = models.DateField("تا تاریخ", null=True, blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "سابقه سکونت"
        verbose_name_plural = "سوابق سکونت"

    def __str__(self):
        return f"{self.name} ({self.unit})"
