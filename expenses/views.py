from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from expenses.forms import ExpenseCategoryForm, ExpenseForm
from expenses.models import Expense, ExpenseCategory


@staff_member_required
@require_http_methods(["GET", "POST"])
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("expenses:list")
    else:
        form = ExpenseForm()
    return render(request, "expenses/expense_form.html", {"form": form, "title": "ثبت هزینه"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def expense_update(request, pk):
    from django.shortcuts import get_object_or_404

    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            return redirect("expenses:list")
    else:
        form = ExpenseForm(instance=expense)
    return render(request, "expenses/expense_form.html", {"form": form, "title": "ویرایش هزینه"})


@login_required
def expense_list(request):
    from django.db.models import Sum

    expenses = Expense.objects.select_related("category")
    category_id = request.GET.get("category", "").strip()
    if category_id:
        expenses = expenses.filter(category_id=category_id)
    filtered_total = expenses.aggregate(s=Sum("amount"))["s"] or 0
    return render(
        request,
        "expenses/expense_list.html",
        {
            "expenses": expenses,
            "categories": ExpenseCategory.objects.all(),
            "filters": {"category": category_id},
            "filtered_total": filtered_total,
        },
    )


def next_category_code():
    from expenses.models import ExpenseCategory

    nums = []
    for code in ExpenseCategory.objects.values_list("code", flat=True):
        try:
            nums.append(int(str(code).split("-")[-1]))
        except (TypeError, ValueError):
            continue
    return f"EXP-{(max(nums) + 1) if nums else 1:03d}"


@staff_member_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.code = next_category_code()
            category.save()
            return redirect("expenses:categories")
    else:
        form = ExpenseCategoryForm()
    categories = ExpenseCategory.objects.all()
    return render(
        request, "expenses/category_list.html",
        {"form": form, "categories": categories},
    )


@staff_member_required
@require_http_methods(["GET", "POST"])
def expense_delete(request, pk):
    from django.shortcuts import get_object_or_404

    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        expense.delete()
        return redirect("expenses:list")
    return render(request, "expenses/expense_confirm_delete.html", {"expense": expense})


@staff_member_required
@require_http_methods(["GET", "POST"])
def category_delete(request, pk):
    from django.contrib import messages
    from django.db.models import ProtectedError
    from django.shortcuts import get_object_or_404

    category = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == "POST":
        try:
            category.delete()
        except ProtectedError:
            messages.error(request, "این نوع مخارج چون هزینه ثبت‌شده دارد قابل حذف نیست.")
            return redirect("expenses:categories")
        return redirect("expenses:categories")
    return render(request, "expenses/category_confirm_delete.html", {"category": category})
