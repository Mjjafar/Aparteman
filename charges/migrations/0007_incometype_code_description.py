from django.db import migrations, models


def assign_codes(apps, schema_editor):
    IncomeType = apps.get_model("charges", "IncomeType")
    for i, obj in enumerate(IncomeType.objects.order_by("pk"), start=1):
        obj.code = f"INC-{i:03d}"
        obj.save(update_fields=["code"])


def unassign_codes(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("charges", "0006_payment_unique_charge_payment_per_unit_month"),
    ]

    operations = [
        migrations.AddField(
            model_name="incometype",
            name="code",
            field=models.CharField(
                default="TMP", max_length=20, verbose_name="کد درآمد"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="incometype",
            name="description",
            field=models.CharField(
                blank=True, default="", max_length=255, verbose_name="شرح درآمد"
            ),
        ),
        migrations.RunPython(assign_codes, unassign_codes),
        migrations.AlterField(
            model_name="incometype",
            name="code",
            field=models.CharField(max_length=20, unique=True, verbose_name="کد درآمد"),
        ),
    ]
