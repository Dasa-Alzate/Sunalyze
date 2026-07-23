
from flask import current_app

from app.gateways.queue.base import (
    JobQueue, STATUS_QUEUED, STATUS_STARTED, STATUS_FINISHED, STATUS_FAILED,
    STATUS_NOT_FOUND,
)
from app.gateways.queue.sync import SyncQueue

__all__ = [
    'JobQueue', 'SyncQueue', 'get_queue',
    'STATUS_QUEUED', 'STATUS_STARTED', 'STATUS_FINISHED', 'STATUS_FAILED',
    'STATUS_NOT_FOUND',
]


def get_queue():
    backend = (current_app.config.get('JOB_QUEUE') or 'sync').lower()
    if backend == 'rq':
        from app.gateways.queue.rq_queue import RQQueue

        return RQQueue.from_config(current_app.config)
    return SyncQueue()
