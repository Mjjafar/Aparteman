from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from charges.forms import PaymentForm
from charges.models import ChargePlan, IncomeType, Payment
from django.shortcuts import get_object_or_404


@staff_member_required
@require_http_methods(["GET", "POST"])
def payment_create(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("charges:list")
    else:
        form = PaymentForm()
    return render(request, "charges/payment_form.html", {"form": form, "title": "ثبت پرداخت"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            return redirect("charges:list")
    else:
        form = PaymentForm(instance=payment)
    return render(request, "charges/payment_form.html", {"form": form, "title": "ویرایش پرداخت"})


@login_required
def payment_list(request):
    from config.jalali_forms import JALALI_MONTH_CHOICES

    payments = Payment.objects.select_related("unit", "income_type")
    if not request.user.is_staff:
        payments = payments.filter(unit__user=request.user)

    year = request.GET.get("year", "").strip()
    month = request.GET.get("month", "").strip()
    income_type_id = request.GET.get("income_type", "").strip()
    unit_no = request.GET.get("unit", "").strip()
    if year:
        payments = payments.filter(year=year)
    if month:
        payments = payments.filter(month=month)
    if income_type_id:
        payments = payments.filter(income_type_id=income_type_id)
    if unit_no:
        payments = payments.filter(unit__number=unit_no)

    years = (
        Payment.objects.order_by("year").values_list("year", flat=True).distinct()
    )
    from units.models import Unit

    return render(
        request,
        "charges/payment_list.html",
        {
            "payments": payments,
            "years": list(years),
            "jalali_months": JALALI_MONTH_CHOICES,
            "income_types": IncomeType.objects.all(),
            "units": Unit.objects.order_by("number"),
            "filters": {"year": year, "month": month, "income_type": income_type_id, "unit": unit_no},
        },
    )


@staff_member_required
def chargeplan_list(request):
    plans = ChargePlan.objects.all()
    return render(request, "charges/chargeplan_list.html", {"plans": plans})


@staff_member_required
@require_http_methods(["GET", "POST"])
def chargeplan_create(request):
    from charges.forms import ChargePlanForm

    if request.method == "POST":
        form = ChargePlanForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("charges:plans")
    else:
        form = ChargePlanForm()
    return render(request, "charges/chargeplan_form.html", {"form": form, "title": "تعریف حق شارژ"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def chargeplan_update(request, pk):
    from charges.forms import ChargePlanForm

    plan = get_object_or_404(ChargePlan, pk=pk)
    if request.method == "POST":
        form = ChargePlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            return redirect("charges:plans")
    else:
        form = ChargePlanForm(instance=plan)
    return render(request, "charges/chargeplan_form.html", {"form": form, "title": "ویرایش حق شارژ"})


@staff_member_required
def incometype_list(request):
    types = IncomeType.objects.all()
    return render(request, "charges/incometype_list.html", {"types": types})


@staff_member_required
@require_http_methods(["GET", "POST"])
def incometype_create(request):
    from charges.forms import IncomeTypeForm

    def next_income_type_code():
        nums = []
        for code in IncomeType.objects.values_list("code", flat=True):
            try:
                nums.append(int(str(code).split("-")[-1]))
            except (TypeError, ValueError):
                continue
        return f"INC-{(max(nums) + 1) if nums else 1:03d}"

    if request.method == "POST":
        form = IncomeTypeForm(request.POST)
        if form.is_valid():
            income_type = form.save(commit=False)
            income_type.code = next_income_type_code()
            income_type.save()
            return redirect("charges:income-types")
    else:
        form = IncomeTypeForm()
    return render(request, "charges/incometype_form.html", {"form": form, "title": "تعریف نوع درآمد"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def payment_delete(request, pk):
    from charges.models import Payment

    payment = get_object_or_404(Payment, pk=pk)
    if request.method == "POST":
        payment.delete()
        return redirect("charges:list")
    return render(request, "charges/payment_confirm_delete.html", {"payment": payment})


@staff_member_required
@require_http_methods(["GET", "POST"])
def chargeplan_delete(request, pk):
    plan = get_object_or_404(ChargePlan, pk=pk)
    if request.method == "POST":
        plan.delete()
        return redirect("charges:plans")
    return render(request, "charges/chargeplan_confirm_delete.html", {"plan": plan})


@staff_member_required
@require_http_methods(["GET", "POST"])
def incometype_delete(request, pk):
    income_type = get_object_or_404(IncomeType, pk=pk)
    if request.method == "POST":
        income_type.delete()
        return redirect("charges:income-types")
    return render(request, "charges/incometype_confirm_delete.html", {"income_type": income_type})


@login_required
def charge_amount(request):
    from django.http import JsonResponse

    from charges.models import ChargePlan

    try:
        plan = ChargePlan.objects.filter(
            unit_id=request.GET.get("unit"),
            year=int(request.GET.get("year", 0)),
            start_month__lte=int(request.GET.get("month", 0)),
            end_month__gte=int(request.GET.get("month", 0)),
        ).first()
    except (TypeError, ValueError):
        plan = None
    return JsonResponse({"amount": plan.amount if plan else None})
