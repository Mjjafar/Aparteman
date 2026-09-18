import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("charges", "0002_incometype_payment_income_type"),
        ("units", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="chargeplan",
            name="unique_plan_year_month",
        ),
        migrations.AddField(
            model_name="chargeplan",
            name="unit",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="charge_plans",
                to="units.unit",
                verbose_name="واحد",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="chargeplan",
            constraint=models.UniqueConstraint(
                fields=("unit", "year", "month"), name="unique_plan_unit_year_month"
            ),
        ),
        migrations.AlterModelOptions(
            name="chargeplan",
            options={
                "ordering": ["unit__number", "-year", "-month"],
                "verbose_name": "تعرفه شارژ",
                "verbose_name_plural": "تعرفه‌های شارژ",
            },
        ),
    ]
