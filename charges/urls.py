from django.urls import path

from charges import views

app_name = "charges"

urlpatterns = [
    path("", views.payment_list, name="list"),
    path("new/", views.payment_create, name="create"),
    path("charge-amount/", views.charge_amount, name="charge-amount"),
    path("<int:pk>/edit/", views.payment_update, name="edit"),
    path("<int:pk>/delete/", views.payment_delete, name="delete"),
    path("plans/", views.chargeplan_list, name="plans"),
    path("plans/new/", views.chargeplan_create, name="plan-create"),
    path("plans/<int:pk>/edit/", views.chargeplan_update, name="plan-edit"),
    path("plans/<int:pk>/delete/", views.chargeplan_delete, name="plan-delete"),
    path("income-types/", views.incometype_list, name="income-types"),
    path("income-types/new/", views.incometype_create, name="income-type-create"),
    path("income-types/<int:pk>/delete/", views.incometype_delete, name="income-type-delete"),
]
