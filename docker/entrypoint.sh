#!/bin/sh
set -e

echo "[entrypoint] esperando a la base de datos..."
python - <<'PY'
import os, sys, time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
if url.startswith("mysql://"):
    url = "mysql+pymysql://" + url[len("mysql://"):]

last = None
for attempt in range(60):
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[entrypoint] base de datos lista")
        sys.exit(0)
    except Exception as exc:
        last = exc
        time.sleep(2)
print(f"[entrypoint] no se pudo conectar a la base de datos: {last}", file=sys.stderr)
sys.exit(1)
PY

echo "[entrypoint] aplicando migraciones (flask db upgrade)..."
flask db upgrade

echo "[entrypoint] arrancando: $*"
exec "$@"
