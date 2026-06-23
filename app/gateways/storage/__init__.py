"""Selección del backend de almacenamiento por configuración.

`get_storage()` devuelve el adaptador indicado por `STORAGE_BACKEND` (`local` por defecto).
El adaptador S3 solo se importa cuando se selecciona, de modo que `boto3` nunca es necesario
para arrancar con el backend local.
"""

from flask import current_app

from app.gateways.storage.base import StorageGateway, StorageError
from app.gateways.storage.local import LocalStorage

__all__ = ['StorageGateway', 'StorageError', 'LocalStorage', 'get_storage']


def get_storage():
    """Devuelve el `StorageGateway` configurado para la app activa."""
    backend = (current_app.config.get('STORAGE_BACKEND') or 'local').lower()
    if backend == 's3':
        from app.gateways.storage.s3 import S3Storage

        return S3Storage.from_config(current_app.config)
    return LocalStorage()
