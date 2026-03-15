# Monitoring Stack

## Что было сломано

- в каталоге не было `.env.example`;
- `docker-compose.yml` читал переменные из корневого `../../.env`, поэтому локальный запуск monitoring-стека был неавтономным;
- при отсутствии переменных PostgreSQL стартовал без `POSTGRES_PASSWORD` и падал;
- Postgres был проброшен на host, что создавало лишние конфликты портов.

## Что исправлено

- добавлен локальный `.env.example`;
- добавлен локальный `.env` для текущего проекта;
- `docker-compose.yml` теперь использует `.env` из `infra/monitoring`;
- PostgreSQL больше не пробрасывается наружу и доступен только внутри Docker network;
- для обязательных переменных добавлен fail-fast через `${VAR:?message}`;
- внешние порты app, Prometheus и Grafana вынесены в переменные.

## Как запустить

```bash
cd infra/monitoring
cp .env.example .env
docker compose up --build
```

## Внешние порты

- ML app: `http://localhost:18000`
- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13000`

## PostgreSQL

- наружу не пробрасывается;
- используется только внутренне по адресу `postgres:5432`;
- это сделано специально, чтобы снизить риск конфликтов host-портов.

## Как решить конфликт портов

Измените значения в `.env`:

- `APP_HOST_PORT`
- `PROMETHEUS_HOST_PORT`
- `GRAFANA_HOST_PORT`

Например:

```bash
APP_HOST_PORT=28000
PROMETHEUS_HOST_PORT=29090
GRAFANA_HOST_PORT=23000
```

## Полный reset

```bash
cd infra/monitoring
docker compose down -v --remove-orphans
docker compose up --build
```
