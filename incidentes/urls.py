from django.urls import path

from . import views

app_name = "incidentes"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("novo/", views.cadastrar, name="cadastrar"),
    path("<int:pk>/editar/", views.editar, name="editar"),
]
