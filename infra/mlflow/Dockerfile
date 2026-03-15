FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/mlflow

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir mlflow==3.3.2 psycopg2-binary==2.9.10

COPY preflight-db.sh /usr/local/bin/mlflow-preflight-db.sh
COPY entrypoint.sh /usr/local/bin/mlflow-entrypoint.sh
RUN chmod +x /usr/local/bin/mlflow-preflight-db.sh /usr/local/bin/mlflow-entrypoint.sh

EXPOSE 5001

ENTRYPOINT ["mlflow-entrypoint.sh"]
CMD ["server"]
