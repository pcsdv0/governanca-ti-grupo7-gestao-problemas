from django.urls import path

from . import views

app_name = "acoes"

urlpatterns = [
    path("problema/<int:problema_pk>/nova/", views.cadastrar, name="cadastrar"),
    path("<int:pk>/status/", views.alterar_status, name="alterar_status"),
]
