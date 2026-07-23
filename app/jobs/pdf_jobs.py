

def generate_document_job(org_id, template_id, project_id, user_id=None):
    from app.services.document_service import DocumentService
    from app.models.user import User

    user = User.query.get(user_id) if user_id else None
    document = DocumentService.generate(org_id, template_id, project_id, user=user)
    return document.to_dict()


def memoria_pdf_job(form_data, org_id=None, user_id=None):
    from app.services.memoria_service import MemoriaService

    return {'org_id': org_id, 'pdf': MemoriaService.generar_pdf(form_data, org_id=org_id)}
