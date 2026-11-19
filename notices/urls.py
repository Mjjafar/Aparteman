from django.urls import path

from notices import views

app_name = "notices"

urlpatterns = [
    path("", views.notice_list, name="list"),
    path("new/", views.notice_create, name="create"),
    path("<int:pk>/", views.notice_detail, name="detail"),
    path("<int:pk>/delete/", views.notice_delete, name="delete"),
]
