# Imagem do sistema para rodar localmente com Docker (plano B da apresentação).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Coleta os estáticos na imagem (a chave aqui é só para o comando rodar).
RUN SECRET_KEY=build-apenas python manage.py collectstatic --no-input

EXPOSE 8000

# Aplica as migrations e sobe o gunicorn.
CMD ["sh", "-c", "python manage.py migrate --no-input && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
