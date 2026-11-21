# Login e logout usam as views prontas do Django. O template de login fica em
# templates/registration/login.html.
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    # Desde o Django 5 o logout só aceita POST (formulário na navbar).
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # RF02: cadastro e edição de Usuários pelo Gestor de TI
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/novo/", views.cadastrar_usuario, name="cadastrar_usuario"),
    path("usuarios/<int:pk>/editar/", views.editar_usuario, name="editar_usuario"),
]
