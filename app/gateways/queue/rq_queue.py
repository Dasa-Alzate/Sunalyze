"""Adaptador de cola sobre Redis + RQ (opcional).

`rq` y `redis` se importan de forma **perezosa** dentro de los métodos para que la app y los
tests arranquen sin la dependencia cuando el backend activo es síncrono. Encola la función
registrada (importable) para que el worker la resuelva; el worker debe correr dentro de un
contexto de aplicación (ver docs/pdf-scalability-research.md).
"""

from app.gateways.queue.base import (
    JobQueue, STATUS_QUEUED, STATUS_STARTED, STATUS_FINISHED, STATUS_FAILED,
    STATUS_NOT_FOUND,
)
from app.jobs import resolve_job

_RQ_STATUS_MAP = {
    'queued': STATUS_QUEUED,
    'deferred': STATUS_QUEUED,
    'scheduled': STATUS_QUEUED,
    'started': STATUS_STARTED,
    'finished': STATUS_FINISHED,
    'failed': STATUS_FAILED,
    'stopped': STATUS_FAILED,
    'canceled': STATUS_FAILED,
}


class RQQueue(JobQueue):
    """Encola los jobs en Redis para que los procese un worker de RQ."""

    is_async = True

    def __init__(self, redis_url, queue_name='pdf', job_timeout=180):
        if not redis_url:
            raise RuntimeError('JOB_QUEUE=rq requiere JOB_QUEUE_REDIS_URL (o REDIS_URL).')
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.job_timeout = job_timeout

    @classmethod
    def from_config(cls, config):
        return cls(
            redis_url=config.get('JOB_QUEUE_REDIS_URL'),
            queue_name=config.get('JOB_QUEUE_NAME', 'pdf'),
            job_timeout=config.get('PDF_JOB_TIMEOUT', 180),
        )

    def _queue(self):
        from redis import Redis
        from rq import Queue

        return Queue(self.queue_name, connection=Redis.from_url(self.redis_url))

    def enqueue(self, job_name, **kwargs):
        func = resolve_job(job_name)
        job = self._queue().enqueue(func, job_timeout=self.job_timeout, kwargs=kwargs)
        return job.id

    def _fetch(self, job_id):
        from rq.job import Job
        from rq.exceptions import NoSuchJobError
        from redis import Redis

        try:
            return Job.fetch(job_id, connection=Redis.from_url(self.redis_url))
        except NoSuchJobError:
            return None

    def get_status(self, job_id):
        job = self._fetch(job_id)
        if job is None:
            return STATUS_NOT_FOUND
        return _RQ_STATUS_MAP.get(job.get_status(), STATUS_QUEUED)

    def get_result(self, job_id):
        job = self._fetch(job_id)
        if job is None:
            return None
        return job.return_value() if hasattr(job, 'return_value') else job.result
