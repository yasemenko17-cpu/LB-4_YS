# Етап 1: Збирач (Builder)
FROM python:3.12-slim AS builder
WORKDIR /app

# Кешування шарів: спершу копіюємо лише файл залежностей
COPY app/requirements.txt ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Етап 2: Кінцевий мінімальний образ
FROM python:3.12-slim
WORKDIR /app

# Створення непривілейованого користувача з числовим ідентифікатором
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser --no-create-home --shell /usr/sbin/nologin appuser

# Копіювання віртуального середовища та коду застосунку з етапу збирача
COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 app/ ./

ENV PATH="/opt/venv/bin:$PATH"

# Перемикання на непривілейованого користувача
USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["python", "app.py"]