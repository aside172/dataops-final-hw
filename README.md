# Итоговое домашнее задание по DataOps

## Описание проекта

В решении собраны:

- инфраструктурные стенды для `MLflow`, `Airflow`, `LakeFS`, `JupyterHub`;
- минимальный рабочий `ML-сервис` на `FastAPI`;
- мониторинг через `Prometheus` и `Grafana`;
- манифесты `Kubernetes`;
- `Helm chart` для деплоя ML-сервиса;
- сценарий для создания нескольких версий prompt в `MLflow Prompt Storage`.

## Цель задания

Отработать полный цикл сборки и развертывания ML-сервиса:

- поднять ключевые DataOps-компоненты;
- подготовить и контейнеризировать ML API;
- подключить логирование и метрики;
- подготовить сервис к развертыванию в Kubernetes;
- упаковать сервис в Helm chart;
- зарегистрировать версии prompt в MLflow.


### Задачи

1. Развернуть `MLflow` через `Dockerfile` и `docker-compose` c `PostgreSQL`.
2. Развернуть `Airflow` через `docker-compose` c `PostgreSQL`, выполнить `db init` и `db migrate`.
3. Развернуть `LakeFS` c `PostgreSQL` и `MinIO`.
4. Развернуть `JupyterHub` через `Dockerfile` и `docker-compose`.
5. Реализовать `ML-сервис` на `FastAPI` с endpoint `/api/v1/predict`.
6. Добавить логирование запросов в `JSON`.
7. Логировать вход, выход, время и версию модели в базе данных.
8. Развернуть `Prometheus` и `Grafana`, добавить endpoint `/metrics`.
9. Подготовить `deployment.yaml`, `service.yaml`, `ingress.yaml` с `startupProbe`, `readinessProbe`, `livenessProbe`.
10. Создать `Helm chart` c настраиваемыми образом и ресурсами.
11. Создать несколько версий prompt в `MLflow Prompt Storage`.

## Что реализовано

### 1. ML-сервис

Реализован сервис кредитного скоринга:

- `POST /api/v1/predict`
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`

Сервис:

- принимает входные признаки `income`, `debt`, `utilization`;
- рассчитывает `risk_score`;
- возвращает бинарный признак `will_default`;
- пишет HTTP-логи в JSON;
- пишет результат инференса в базу данных;
- экспортирует метрики для Prometheus.

### 2. MLflow

В каталоге `infra/mlflow/` подготовлены:

- `Dockerfile` на базе `python:3.11-slim`;
- `docker-compose.yml`;
- `.env.example`.

Также добавлен скрипт `scripts/bootstrap_prompt_storage.py` для регистрации нескольких версий prompt через API MLflow.

### 3. Airflow

В каталоге `infra/airflow/` подготовлены:

- `docker-compose.yml` с `PostgreSQL`;
- инициализационный сервис только с валидной для Airflow 3 командой `airflow db migrate`;
- сервисы `api-server`, `scheduler`, `dag-processor`, `triggerer`;
- пример DAG `hello_dataops.py`.

### 4. LakeFS

В каталоге `infra/lakefs/` подготовлены:

- `docker-compose.yml`;
- `PostgreSQL`;
- `MinIO`;
- bootstrap bucket через `minio/mc`;
- конфигурация окружения для lakeFS.

### 5. JupyterHub

В каталоге `infra/jupyterhub/` подготовлены:

- `Dockerfile` на базе `python:3.14-slim`;
- установка `jupyterhub`, `jupyterlab`, `configurable-http-proxy`;
- `docker-compose.yml`;
- `jupyterhub_config.py`;
- вход под пользователем `admin`, запуск через JupyterLab.

### 6. Мониторинг

В каталоге `infra/monitoring/` подготовлены:

- `docker-compose.yml`;
- локальный `.env.example`;
- локальный README со стеком запуска;
- `prometheus.yml`;
- provisioning для Grafana datasource;
- provisioning для dashboard;
- готовый dashboard JSON.

### 7. Kubernetes и Helm

Подготовлены:

- `k8s/deployment.yaml`
- `k8s/service.yaml`
- `k8s/ingress.yaml`
- `helm/ml-service/*`

В манифестах и chart добавлены:

- `startupProbe`
- `readinessProbe`
- `livenessProbe`
- настраиваемая версия Docker-образа
- настраиваемые ресурсы CPU и memory

## Подготовка окружения

### Локальный Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Как запустить проект

### 1. ML-сервис локально

```bash
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Проверка:

```bash
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/api/v1/predict \
  -H 'Content-Type: application/json' \
  -d '{"income": 4500, "debt": 1800, "utilization": 0.42}'
```

### 2. ML-сервис через Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

### 3. MLflow

```bash
cd infra/mlflow
cp .env.example .env
docker compose up --build
```

MLflow будет доступен по адресу:

```bash
http://localhost:5001
```

После старта:

```bash
docker compose exec mlflow python /opt/project-scripts/bootstrap_prompt_storage.py
```

Полный reset БД MLflow при необходимости:

```bash
cd infra/mlflow
docker compose down -v --remove-orphans
rm -rf ../../artifacts/mlflow
docker compose up --build
```

Ручная диагностика PostgreSQL для MLflow:

```bash
cd infra/mlflow
docker compose exec mlflow-postgres psql -U mlflow -d mlflow -c "SELECT * FROM alembic_version;"
docker compose exec mlflow-postgres psql -U mlflow -d mlflow -c "\\dt"
docker compose exec mlflow-postgres psql -U mlflow -d mlflow -c "SELECT to_regclass('public.metrics');"
```

### 4. Airflow

```bash
cd infra/airflow
cp .env.example .env
docker compose up --remove-orphans
```

Airflow UI будет доступен на:

```bash
http://localhost:8081
```

Полный reset Airflow volume при необходимости:

```bash
cd infra/airflow
docker compose down -v --remove-orphans
rm -rf ../../airflow-logs
docker compose up --remove-orphans
```

### 5. LakeFS

```bash
cd infra/lakefs
cp .env.example .env
docker compose up
```

После запуска:

- MinIO console: `http://localhost:9001`
- LakeFS UI: `http://localhost:8001`

### 6. JupyterHub

```bash
cd infra/jupyterhub
cp .env.example .env
docker compose up --build
```

JupyterHub будет доступен на `http://localhost:8002`.

### 7. Мониторинг

```bash
cd infra/monitoring
cp .env.example .env
docker compose up --build
```

После запуска:

- Prometheus: `http://localhost:19090`
- Grafana: `http://localhost:13000`
- ML app: `http://localhost:18000`

### 8. Kubernetes

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 9. Helm

```bash
helm install ml-risk ./helm/ml-service
helm upgrade --install ml-risk ./helm/ml-service \
  --set image.repository=ghcr.io/example/ml-risk-service \
  --set image.tag=2026.03.15
```

## Как тестировать

```bash
source venv/bin/activate
pytest -q
```