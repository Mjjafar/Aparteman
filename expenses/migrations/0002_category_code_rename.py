from django.db import migrations, models


RENAMES = {
    "قبض آب": "قبض آب مشترک کل ساختمان",
    "قبض گاز": "قبض گاز مشترک کل ساختمان",
    "قبض برق": "قبض برق مشاعات ساختمان",
    "نظافت": "نظافت راه پله ها و مشاعات ساختمان",
}


def assign_codes_and_renames(apps, schema_editor):
    ExpenseCategory = apps.get_model("expenses", "ExpenseCategory")
    for obj in ExpenseCategory.objects.order_by("pk"):
        obj.code = f"EXP-{obj.pk:03d}"
        if obj.title in RENAMES:
            obj.title = RENAMES[obj.title]
        obj.save(update_fields=["code", "title"])


def reverse_codes_and_renames(apps, schema_editor):
    ExpenseCategory = apps.get_model("expenses", "ExpenseCategory")
    reverse = {v: k for k, v in RENAMES.items()}
    for obj in ExpenseCategory.objects.order_by("pk"):
        if obj.title in reverse:
            obj.title = reverse[obj.title]
        obj.save(update_fields=["title"])


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="expensecategory",
            name="code",
            field=models.CharField(default="TMP", max_length=20, verbose_name="کد"),
            preserve_default=False,
        ),
        migrations.RunPython(assign_codes_and_renames, reverse_codes_and_renames),
        migrations.AlterField(
            model_name="expensecategory",
            name="code",
            field=models.CharField(max_length=20, unique=True, verbose_name="کد"),
        ),
    ]
