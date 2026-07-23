
from flask import current_app

from app.gateways.storage.base import StorageGateway, StorageError
from app.gateways.storage.local import LocalStorage

__all__ = ['StorageGateway', 'StorageError', 'LocalStorage', 'get_storage']


def get_storage():
    backend = (current_app.config.get('STORAGE_BACKEND') or 'local').lower()
    if backend == 's3':
        from app.gateways.storage.s3 import S3Storage

        return S3Storage.from_config(current_app.config)
    return LocalStorage()
