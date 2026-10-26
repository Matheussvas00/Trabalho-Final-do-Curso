FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# --nostatic: deixa o WhiteNoise servir /static/ a partir de staticfiles/, como em produção
CMD ["sh", "-c", "python manage.py migrate --no-input && python manage.py runserver --nostatic 0.0.0.0:8000"]
