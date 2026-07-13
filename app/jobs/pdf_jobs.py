"""Funciones de trabajo (jobs) de generación de PDF.

Reciben tipos serializables (ids, dicts) para ser compatibles con RQ, y encapsulan la llamada
al dominio. El adaptador síncrono las ejecuta inline; el de RQ las delega a un worker. Ambos
requieren un contexto de aplicación activo (el request en sync; el bootstrap del worker en RQ).
"""


def generate_document_job(org_id, template_id, project_id, user_id=None):
    """Genera y persiste un `GeneratedDocument`; devuelve su representación serializable."""
    from app.services.document_service import DocumentService
    from app.models.user import User

    user = User.query.get(user_id) if user_id else None
    document = DocumentService.generate(org_id, template_id, project_id, user=user)
    return document.to_dict()


def memoria_pdf_job(form_data, org_id=None, user_id=None):
    """Genera la memoria técnica y devuelve `{'org_id', 'pdf'}`.

    El `org_id` queda ligado al resultado en el encolado para que la ruta de estado
    pueda rechazar el sondeo de un job ajeno (evita IDOR entre organizaciones)."""
    from app.services.memoria_service import MemoriaService

    return {'org_id': org_id, 'pdf': MemoriaService.generar_pdf(form_data)}
