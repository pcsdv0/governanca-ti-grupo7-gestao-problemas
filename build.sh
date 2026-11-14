#!/usr/bin/env bash
# Build do Render: roda a cada deploy (configurado em render.yaml).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# O plano gratuito do Render não tem terminal (shell). Por isso o administrador
# é criado aqui, a partir das variáveis DJANGO_SUPERUSER_USERNAME,
# DJANGO_SUPERUSER_EMAIL e DJANGO_SUPERUSER_PASSWORD (definidas no painel).
# Se o usuário já existir, o comando falha e seguimos normalmente.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --no-input || echo "Administrador já existe."
fi

# Dados de demonstração (opcional): defina CARREGAR_DEMO=True no painel do Render.
# O comando não faz nada se já houver Incidentes, então pode rodar a cada deploy.
if [ "$CARREGAR_DEMO" = "True" ]; then
  python manage.py carregar_demo
fi
