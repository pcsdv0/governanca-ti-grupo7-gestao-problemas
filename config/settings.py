"""
Configurações do projeto Gestão de Problemas (Grupo 7).

Tudo que muda entre ambientes (desenvolvimento, Docker, Render) vem de variáveis
de ambiente lidas com python-decouple. Veja o arquivo `.env.example`.
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Segurança -----------------------------------------------------------------
DEBUG = config("DEBUG", default=False, cast=bool)

# Em desenvolvimento (DEBUG=True) há uma chave padrão só para facilitar o início.
# Em produção a variável SECRET_KEY é obrigatória: sem ela o Django não sobe.
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-chave-apenas-para-desenvolvimento" if DEBUG else None,
)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# O Render informa o domínio público do serviço nesta variável.
RENDER_EXTERNAL_HOSTNAME = config("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Ligado apenas quando o site é servido por HTTPS (Render). No Docker local fica
# desligado, senão os cookies seguros impediriam o login em http://localhost.
USAR_HTTPS = config("USAR_HTTPS", default=False, cast=bool)
if USAR_HTTPS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# --- Aplicações ----------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "simple_history",
    # Apps do projeto (responsáveis em docs/EQUIPE.md)
    "contas",
    "sistemas",
    "incidentes",
    "problemas",
    "acoes",
    "kedb",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serve os arquivos estáticos em produção sem servidor extra.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Registra o usuário logado no histórico (simple-history): "quem alterou".
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Banco de dados ------------------------------------------------------------
# Sem DATABASE_URL usa SQLite (desenvolvimento). Com DATABASE_URL usa o banco
# indicado, por exemplo PostgreSQL no Render ou no docker-compose.
DATABASE_URL = config("DATABASE_URL", default="")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticação --------------------------------------------------------------
# Modelo de usuário customizado com o campo "perfil" (ver contas/models.py).
AUTH_USER_MODEL = "contas.Usuario"

LOGIN_URL = "contas:login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "contas:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalização -------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Recife"
USE_I18N = True
USE_TZ = True

# --- Arquivos estáticos --------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Compressão sem manifesto: mais simples e não exige collectstatic nos testes.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
