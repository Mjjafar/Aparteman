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
    expenses = Expense.objects.select_related("category")
    return render(request, "expenses/expense_list.html", {"expenses": expenses})


@staff_member_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
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
