"""Adaptador de cola síncrono (DEFAULT): ejecuta el job inline.

Reproduce el comportamiento actual: al encolar, el job corre en el mismo request y su
resultado queda disponible de inmediato. Las excepciones **propagan** para conservar el mismo
contrato de error que la generación síncrona previa. Los resultados se guardan en un buffer
acotado a nivel de clase para que un posible sondeo posterior en el mismo proceso los
encuentre.
"""

import uuid
from collections import OrderedDict

from app.gateways.queue.base import (
    JobQueue, STATUS_FINISHED, STATUS_NOT_FOUND,
)
from app.jobs import resolve_job


class SyncQueue(JobQueue):
    """Ejecuta los jobs de forma inmediata y bloqueante."""

    is_async = False

    _RESULTS = OrderedDict()
    _MAX_RESULTS = 200

    def enqueue(self, job_name, **kwargs):
        func = resolve_job(job_name)
        result = func(**kwargs)
        job_id = uuid.uuid4().hex
        self._store(job_id, result)
        return job_id

    @classmethod
    def _store(cls, job_id, result):
        cls._RESULTS[job_id] = result
        while len(cls._RESULTS) > cls._MAX_RESULTS:
            cls._RESULTS.popitem(last=False)

    def get_status(self, job_id):
        return STATUS_FINISHED if job_id in self._RESULTS else STATUS_NOT_FOUND

    def get_result(self, job_id):
        return self._RESULTS.get(job_id)
