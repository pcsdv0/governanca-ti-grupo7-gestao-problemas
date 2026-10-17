# Login e logout usam as views prontas do Django. O template de login fica em
# templates/registration/login.html.
from django.contrib.auth import views as auth_views
from django.urls import path

app_name = "contas"

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    # Desde o Django 5 o logout só aceita POST (formulário na navbar).
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
