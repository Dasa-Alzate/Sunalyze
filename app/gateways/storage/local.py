"""Adaptador de almacenamiento en filesystem local (DEFAULT).

Replica EXACTO el layout histórico de `DocumentService`: los artefactos viven en
`instance/generated/<org_id>/<key>` y la `ref` es la ruta relativa a `instance_path`
(idéntica al valor que `GeneratedDocument.pdf_path` ha guardado siempre). Así, con el backend
por defecto, el comportamiento y las rutas en disco no cambian.
"""

import os

from flask import current_app

from app.gateways.storage.base import StorageGateway

GENERATED_SUBDIR = 'generated'


class LocalStorage(StorageGateway):
    """Guarda los PDF bajo `instance/generated/<org_id>/<key>`."""

    def _base_dir(self):
        base = os.path.join(current_app.instance_path, GENERATED_SUBDIR)
        os.makedirs(base, exist_ok=True)
        return base

    def save(self, org_id, key, data):
        org_dir = os.path.join(self._base_dir(), str(org_id))
        os.makedirs(org_dir, exist_ok=True)
        abs_path = os.path.join(org_dir, key)
        with open(abs_path, 'wb') as handle:
            handle.write(data)
        return os.path.relpath(abs_path, current_app.instance_path)

    def read(self, ref):
        abs_path = os.path.join(current_app.instance_path, ref)
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(ref)
        with open(abs_path, 'rb') as handle:
            return handle.read()

    def exists(self, ref):
        abs_path = os.path.join(current_app.instance_path, ref)
        return os.path.isfile(abs_path)

    def url(self, ref):
        return None
