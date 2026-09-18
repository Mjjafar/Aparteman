from django.urls import path

from expenses import views

app_name = "expenses"

urlpatterns = [
    path("", views.expense_list, name="list"),
    path("new/", views.expense_create, name="create"),
    path("<int:pk>/edit/", views.expense_update, name="edit"),
    path("<int:pk>/delete/", views.expense_delete, name="delete"),
    path("categories/", views.category_create, name="categories"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category-delete"),
]
