from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


def copy_month_forward(apps, schema_editor):
    ChargePlan = apps.get_model("charges", "ChargePlan")
    for plan in ChargePlan.objects.all():
        plan.start_month = plan.month
        plan.end_month = plan.month
        plan.save(update_fields=["start_month", "end_month"])


def copy_month_backward(apps, schema_editor):
    ChargePlan = apps.get_model("charges", "ChargePlan")
    for plan in ChargePlan.objects.all():
        plan.month = plan.start_month
        plan.save(update_fields=["month"])


class Migration(migrations.Migration):
    dependencies = [
        ("charges", "0003_chargeplan_unit"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="chargeplan",
            name="unique_plan_unit_year_month",
        ),
        migrations.AddField(
            model_name="chargeplan",
            name="start_month",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[MinValueValidator(1), MaxValueValidator(12)],
                verbose_name="ماه شروع",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="chargeplan",
            name="end_month",
            field=models.PositiveSmallIntegerField(
                default=1,
                validators=[MinValueValidator(1), MaxValueValidator(12)],
                verbose_name="ماه پایان",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copy_month_forward, copy_month_backward),
        migrations.RemoveField(
            model_name="chargeplan",
            name="month",
        ),
        migrations.AddConstraint(
            model_name="chargeplan",
            constraint=models.UniqueConstraint(
                fields=("unit", "year", "start_month", "end_month"),
                name="unique_plan_unit_year_months",
            ),
        ),
        migrations.AlterModelOptions(
            name="chargeplan",
            options={
                "ordering": ["unit__number", "-year", "-start_month"],
                "verbose_name": "تعرفه شارژ",
                "verbose_name_plural": "تعرفه‌های شارژ",
            },
        ),
    ]
