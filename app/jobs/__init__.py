
from app.jobs.pdf_jobs import generate_document_job, memoria_pdf_job

JOB_REGISTRY = {
    'generate_document': generate_document_job,
    'memoria_pdf': memoria_pdf_job,
}


def resolve_job(job_name):
    try:
        return JOB_REGISTRY[job_name]
    except KeyError as exc:
        raise KeyError(f'Job no registrado: {job_name}') from exc
