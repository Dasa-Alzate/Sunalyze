"""Punto de entrada WSGI para producción (gunicorn).

A diferencia de run.py (servidor de desarrollo), aquí se envuelve la app con
ProxyFix para que, detrás de un reverse proxy (nginx/Caddy/balanceador), Flask
lea la IP y el esquema reales desde las cabeceras X-Forwarded-* en lugar de la
IP del proxy. Esto es lo que necesitan el rate limiting y cualquier filtro por IP.
"""

from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
