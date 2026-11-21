from django.urls import path

from . import views

app_name = "problemas"

urlpatterns = [
    path("<int:pk>/validar-solucao/", views.validar_solucao, name="validar_solucao"),
    path("", views.listar, name="listar"),
    path("novo/", views.cadastrar, name="cadastrar"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/vincular/", views.vincular, name="vincular"),
    path("<int:pk>/atribuir/", views.atribuir, name="atribuir"),
    path("<int:pk>/status/", views.alterar_status, name="alterar_status"),
    path("<int:pk>/causa-raiz/", views.registrar_causa_raiz, name="registrar_causa_raiz"),
]
