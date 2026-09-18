from django.urls import path

from units import views

app_name = "units"

urlpatterns = [
    path("", views.unit_list, name="list"),
    path("new/", views.unit_create, name="create"),
    path("owners/", views.owner_list, name="owners"),
    path("<int:pk>/", views.unit_detail, name="detail"),
    path("<int:pk>/edit/", views.unit_update, name="edit"),
    path("<int:pk>/delete/", views.unit_delete, name="delete"),
    path("<int:pk>/set-login/", views.set_unit_login, name="set-login"),
    path("<int:pk>/change-owner/", views.unit_change_owner, name="change-owner"),
    path("<int:pk>/change-tenant/", views.unit_change_tenant, name="change-tenant"),
    path("<int:pk>/past-owner/", views.unit_past_owner, name="past-owner"),
    path("<int:pk>/past-tenant/", views.unit_past_tenant, name="past-tenant"),
    path("ownership/<int:pk>/delete/", views.ownership_delete, name="ownership-delete"),
    path("tenancy/<int:pk>/delete/", views.tenancy_delete, name="tenancy-delete"),
]
