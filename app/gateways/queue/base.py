"""Interfaz de cola de trabajos desacoplada de la infraestructura.

Un `JobQueue` encola una tarea (por nombre registrado) y permite consultar su estado y
resultado. El adaptador por defecto la ejecuta inline (comportamiento síncrono actual); el
adaptador RQ la delega a un worker de Redis. El dominio solo conoce esta interfaz.

Estados normalizados: `queued`, `started`, `finished`, `failed`, `not_found`.
"""

STATUS_QUEUED = 'queued'
STATUS_STARTED = 'started'
STATUS_FINISHED = 'finished'
STATUS_FAILED = 'failed'
STATUS_NOT_FOUND = 'not_found'


class JobQueue:
    """Contrato mínimo que cumplen todos los adaptadores de cola."""

    is_async = False

    def enqueue(self, job_name, **kwargs):
        """Encola el job registrado como `job_name` y devuelve su `job_id`."""
        raise NotImplementedError

    def get_status(self, job_id):
        """Devuelve el estado normalizado del job."""
        raise NotImplementedError

    def get_result(self, job_id):
        """Devuelve el resultado del job (o `None` si no está disponible)."""
        raise NotImplementedError
