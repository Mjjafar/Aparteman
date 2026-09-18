from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from units.forms import UnitUserForm
from units.models import Unit


@staff_member_required
@require_http_methods(["GET", "POST"])
def set_unit_login(request, pk):
    return redirect("units:edit", pk=pk)


@staff_member_required
def unit_list(request):
    units = Unit.objects.all().order_by("number")
    return render(request, "units/unit_list.html", {"units": units})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_create(request):
    from units.forms import UnitForm

    if request.method == "POST":
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save()
            return redirect("units:list")
    else:
        form = UnitForm()
    return render(request, "units/unit_form.html", {"form": form, "title": "ثبت واحد جدید"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_update(request, pk):
    from units.forms import UnitFullForm

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        form = UnitFullForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            return redirect("units:list")
    else:
        form = UnitFullForm(instance=unit)
    return render(request, "units/unit_form.html", {"form": form, "title": f"ویرایش {unit}", "unit": unit})


@staff_member_required
def owner_list(request):
    units = Unit.objects.all().order_by("number")
    return render(request, "units/owner_list.html", {"units": units})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_delete(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        if unit.user_id is not None:
            unit.user.delete()
        unit.delete()
        return redirect("units:list")
    return render(request, "units/unit_confirm_delete.html", {"unit": unit})


@staff_member_required
def unit_detail(request, pk):
    from dashboard.jalali import to_fa_digits
    import jdatetime

    unit = get_object_or_404(Unit, pk=pk)

    def jdate(d):
        if not d:
            return "—"
        try:
            return to_fa_digits(jdatetime.date.fromgregorian(date=d).strftime("%Y/%m/%d"))
        except (ValueError, AttributeError):
            return str(d)

    return render(
        request,
        "units/unit_detail.html",
        {"unit": unit, "jdate": jdate},
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_change_owner(request, pk):
    from units.forms import OwnershipChangeForm
    from units.models import OwnershipHistory

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        form = OwnershipChangeForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"]
            open_rec = unit.ownerships.filter(end_date__isnull=True).first()
            if open_rec:
                open_rec.end_date = start
                open_rec.save()
            OwnershipHistory.objects.create(
                unit=unit, name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"], start_date=start,
            )
            unit.owner_name = form.cleaned_data["name"]
            unit.owner_phone = form.cleaned_data["phone"]
            unit.save()
            return redirect("units:detail", pk=unit.pk)
    else:
        form = OwnershipChangeForm()
    return render(request, "units/change_owner.html", {"form": form, "unit": unit})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_change_tenant(request, pk):
    from units.forms import TenancyChangeForm
    from units.models import TenancyHistory

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        form = TenancyChangeForm(request.POST)
        if form.is_valid():
            start = form.cleaned_data["start_date"]
            open_rec = unit.tenancies.filter(end_date__isnull=True).first()
            if open_rec:
                open_rec.end_date = start
                open_rec.save()
            TenancyHistory.objects.create(
                unit=unit, name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"], start_date=start,
            )
            unit.tenant_name = form.cleaned_data["name"]
            unit.tenant_phone = form.cleaned_data["phone"]
            unit.save()
            return redirect("units:detail", pk=unit.pk)
    else:
        form = TenancyChangeForm()
    return render(request, "units/change_tenant.html", {"form": form, "unit": unit})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_past_owner(request, pk):
    from units.forms import OwnershipPastForm
    from units.models import OwnershipHistory

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        form = OwnershipPastForm(request.POST)
        if form.is_valid():
            OwnershipHistory.objects.create(
                unit=unit, name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data.get("end_date"),
            )
            return redirect("units:detail", pk=unit.pk)
    else:
        form = OwnershipPastForm()
    return render(request, "units/past_owner.html", {"form": form, "unit": unit})


@staff_member_required
@require_http_methods(["GET", "POST"])
def unit_past_tenant(request, pk):
    from units.forms import TenancyPastForm
    from units.models import TenancyHistory

    unit = get_object_or_404(Unit, pk=pk)
    if request.method == "POST":
        form = TenancyPastForm(request.POST)
        if form.is_valid():
            TenancyHistory.objects.create(
                unit=unit, name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data.get("end_date"),
            )
            return redirect("units:detail", pk=unit.pk)
    else:
        form = TenancyPastForm()
    return render(request, "units/past_tenant.html", {"form": form, "unit": unit})


@staff_member_required
@require_http_methods(["GET", "POST"])
def ownership_delete(request, pk):
    from units.models import OwnershipHistory

    rec = get_object_or_404(OwnershipHistory, pk=pk)
    unit_pk = rec.unit_id
    if request.method == "POST":
        rec.delete()
        return redirect("units:detail", pk=unit_pk)
    return render(request, "units/history_confirm_delete.html", {"rec": rec, "kind": "مالکیت"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def tenancy_delete(request, pk):
    from units.models import TenancyHistory

    rec = get_object_or_404(TenancyHistory, pk=pk)
    unit_pk = rec.unit_id
    if request.method == "POST":
        rec.delete()
        return redirect("units:detail", pk=unit_pk)
    return render(request, "units/history_confirm_delete.html", {"rec": rec, "kind": "سکونت"})
