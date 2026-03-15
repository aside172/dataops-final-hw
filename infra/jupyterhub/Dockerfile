FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/jupyterhub

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl nodejs npm \
    && npm install -g configurable-http-proxy \
    && pip install --no-cache-dir jupyterhub==5.3.0 jupyterlab==4.4.6 \
    && useradd -m -s /bin/bash admin \
    && rm -rf /var/lib/apt/lists/*

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

EXPOSE 8000

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
