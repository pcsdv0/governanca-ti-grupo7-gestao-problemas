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
