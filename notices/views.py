import jdatetime
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from notices.forms import NoticeForm
from notices.models import Notice, NoticeRow
from notices.services import attach_status, build_rows, totals_for


@staff_member_required
def notice_list(request):
    notices = Notice.objects.select_related("created_by").prefetch_related("rows")
    return render(request, "notices/notice_list.html", {"notices": notices})


@staff_member_required
@require_http_methods(["GET", "POST"])
def notice_create(request):
    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data["year"]
            months = sorted(form.cleaned_data["months"])
            work_title = form.cleaned_data["work_title"].strip()
            work_amount = form.cleaned_data["work_amount"] or 0

            rows, missing = build_rows(year, months, work_amount)

            if request.POST.get("action") == "preview":
                rows = attach_status(rows, year, months)
                draft = Notice(
                    year=year,
                    months=months,
                    work_title=work_title,
                    work_amount=work_amount or None,
                )
                return render(
                    request,
                    "notices/notice_form.html",
                    {
                        "form": form,
                        "title": "اطلاعیه جدید",
                        "draft": draft,
                        "preview_rows": rows,
                        "totals": totals_for(rows),
                        "missing_plans": missing,
                    },
                )

            with transaction.atomic():
                notice = Notice.objects.create(
                    year=year,
                    months=months,
                    work_title=work_title,
                    work_amount=work_amount or None,
                    created_by=request.user,
                )
                NoticeRow.objects.bulk_create(
                    [
                        NoticeRow(
                            notice=notice,
                            unit=row["unit"],
                            resident_name=row["resident_name"],
                            charge_amount=row["charge_amount"],
                            work_share=row["work_share"],
                        )
                        for row in rows
                    ]
                )
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm(initial={"year": jdatetime.date.today().year})
    return render(
        request, "notices/notice_form.html", {"form": form, "title": "اطلاعیه جدید"}
    )


@staff_member_required
def notice_detail(request, pk):
    notice = get_object_or_404(Notice.objects.prefetch_related("rows__unit"), pk=pk)
    rows = [
        {
            "unit": row.unit,
            "resident_name": row.resident_name,
            "charge_amount": row.charge_amount,
            "work_share": row.work_share,
        }
        for row in notice.rows.all()
    ]
    rows = attach_status(rows, notice.year, notice.month_numbers())
    return render(
        request,
        "notices/notice_detail.html",
        {"notice": notice, "rows": rows, "totals": totals_for(rows)},
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == "POST":
        notice.delete()
        return redirect("notices:list")
    return render(
        request, "notices/notice_confirm_delete.html", {"notice": notice}
    )
