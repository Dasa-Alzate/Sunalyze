
STATUS_QUEUED = 'queued'
STATUS_STARTED = 'started'
STATUS_FINISHED = 'finished'
STATUS_FAILED = 'failed'
STATUS_NOT_FOUND = 'not_found'


class JobQueue:

    is_async = False

    def enqueue(self, job_name, **kwargs):
        raise NotImplementedError

    def get_status(self, job_id):
        raise NotImplementedError

    def get_result(self, job_id):
        raise NotImplementedError
