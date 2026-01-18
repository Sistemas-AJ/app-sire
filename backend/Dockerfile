FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Lima

# Instala tzdata (y evita prompts interactivos)
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY req.txt /app/req.txt
RUN pip install --no-cache-dir -r /app/req.txt

# Playwright (tu base ya trae browsers, pero lo dejas “a prueba de balas”)
RUN playwright install --with-deps chromium

COPY . /app

EXPOSE 8654
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "api.main:app", "--bind", "0.0.0.0:8654", "--workers", "1", "--timeout", "120", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-", "--capture-output"]