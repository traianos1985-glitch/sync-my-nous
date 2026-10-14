FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data apps forge executor/plugins && \
    useradd -m -u 10001 nous && chown -R nous:nous /app
USER nous

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/health || exit 1

# The app starts in-process background loops; use one worker until loops are externalized.
# executor.wsgi:app wraps chat() so unified intent runs before legacy browser_operator.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "gthread", "--threads", "8", "--workers", "1", "--timeout", "120", "--access-logfile", "-", "executor.wsgi:app"]
