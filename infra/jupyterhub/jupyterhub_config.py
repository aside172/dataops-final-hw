import os

from jupyterhub.auth import DummyAuthenticator


c = get_config()  # noqa: F821

c.JupyterHub.bind_url = "http://0.0.0.0:8000"
c.JupyterHub.spawner_class = "simple"
c.JupyterHub.authenticator_class = DummyAuthenticator
c.JupyterHub.admin_access = True
c.JupyterHub.db_url = "sqlite:////srv/jupyterhub_data/jupyterhub.sqlite"
c.JupyterHub.cookie_secret_file = "/srv/jupyterhub_data/jupyterhub_cookie_secret"
c.DummyAuthenticator.password = os.getenv("JUPYTERHUB_ADMIN_PASSWORD", "admin")
c.Authenticator.admin_users = {os.getenv("JUPYTERHUB_ADMIN_USER", "admin")}
c.Spawner.default_url = "/lab"
c.Spawner.args = ["--allow-root"]
c.JupyterHub.shutdown_on_logout = False
