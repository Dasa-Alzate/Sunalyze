"""Interfaz de almacenamiento de artefactos (PDF) desacoplada de la infraestructura.

Un `StorageGateway` guarda bytes bajo una clave org-scoped y devuelve una `ref` opaca que
luego permite releer, comprobar existencia y (opcionalmente) obtener una URL. Los adaptadores
concretos (local, S3/MinIO) se seleccionan por configuración sin que el dominio los conozca.
"""


class StorageError(Exception):
    """Fallo genérico de un backend de almacenamiento."""


class StorageGateway:
    """Contrato mínimo que cumplen todos los adaptadores de almacenamiento."""

    def save(self, org_id, key, data):
        """Persiste `data` (bytes) bajo `(org_id, key)` y devuelve la `ref` para releerlo."""
        raise NotImplementedError

    def read(self, ref):
        """Devuelve los bytes guardados. Lanza `FileNotFoundError` si la `ref` no existe."""
        raise NotImplementedError

    def exists(self, ref):
        """Indica si la `ref` apunta a un artefacto existente."""
        raise NotImplementedError

    def url(self, ref):
        """URL directa/presignada del artefacto, o `None` si el backend no la ofrece."""
        return None
