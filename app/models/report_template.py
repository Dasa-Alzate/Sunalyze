"""Modelos del constructor de plantillas de documentos (a nivel de organización).

Patrón system/oficial igual que `Catalog`: una plantilla con `org_id` NULL y `scope='system'`
es del banco oficial (solo lectura); con `org_id` presente pertenece al workspace. La
biblioteca de una organización son sus `TemplateInstallation` (plantillas seleccionadas, con
favorito, categoría y etiquetas). Quitar de la selección borra solo la fila de instalación,
nunca la plantilla system.

`GeneratedDocument` registra cada PDF producido a partir de una plantilla + un proyecto,
fijando la versión de plantilla usada (`template_version_id`) para trazabilidad y un hash
SHA-256 de los bytes como prueba de integridad (mismo patrón que `MemoriaSignature`).
"""

import json

from app.extensions import db
from .database import BaseModel


_PROJECT_GROUP_NAMES = ('project', 'panel', 'inverter', 'battery', 'wire', 'user', 'org')
_POSVENTA_GROUP_NAMES = ('installation', 'maintenance', 'incident')

DOCUMENT_KIND_REGISTRY = [
    {'key': 'memoria_calculo', 'label': 'Memoria de cálculo',
     'var_groups': _PROJECT_GROUP_NAMES},
    {'key': 'documento_legal', 'label': 'Documento legal',
     'var_groups': _PROJECT_GROUP_NAMES + _POSVENTA_GROUP_NAMES},
    {'key': 'propuesta_comercial', 'label': 'Propuesta comercial',
     'var_groups': _PROJECT_GROUP_NAMES + ('finance',)},
    {'key': 'analisis_caso', 'label': 'Análisis de caso',
     'var_groups': _PROJECT_GROUP_NAMES},
    {'key': 'contrato', 'label': 'Contrato',
     'var_groups': _PROJECT_GROUP_NAMES + ('finance',) + _POSVENTA_GROUP_NAMES},
    {'key': 'certificado', 'label': 'Certificado',
     'var_groups': _PROJECT_GROUP_NAMES + _POSVENTA_GROUP_NAMES},
    {'key': 'informe_mantenimiento', 'label': 'Informe de mantenimiento',
     'var_groups': _PROJECT_GROUP_NAMES + _POSVENTA_GROUP_NAMES},
    {'key': 'solicitud_conexion', 'label': 'Solicitud de conexión',
     'var_groups': _PROJECT_GROUP_NAMES},
]

_DOCUMENT_KIND_BY_KEY = {entry['key']: entry for entry in DOCUMENT_KIND_REGISTRY}


class DocumentKind:
    """Registro de tipos de documento (code-as-config, no tabla).

    Cada kind declara su `key`, `label` y los grupos de variables que expone (`var_groups`).
    Añadir un kind = una entrada en `DOCUMENT_KIND_REGISTRY`. Las constantes y `ALL` se conservan
    por compatibilidad con el código que las referencia.
    """

    MEMORIA_CALCULO = 'memoria_calculo'
    DOCUMENTO_LEGAL = 'documento_legal'
    PROPUESTA_COMERCIAL = 'propuesta_comercial'
    ANALISIS_CASO = 'analisis_caso'
    CONTRATO = 'contrato'
    CERTIFICADO = 'certificado'
    INFORME_MANTENIMIENTO = 'informe_mantenimiento'
    SOLICITUD_CONEXION = 'solicitud_conexion'

    ALL = tuple(entry['key'] for entry in DOCUMENT_KIND_REGISTRY)

    @staticmethod
    def is_valid(key):
        return key in _DOCUMENT_KIND_BY_KEY

    @staticmethod
    def label(key):
        entry = _DOCUMENT_KIND_BY_KEY.get(key)
        return entry['label'] if entry else key

    @staticmethod
    def meta(key):
        return _DOCUMENT_KIND_BY_KEY.get(key)

    @staticmethod
    def all_meta():
        return [dict(entry) for entry in DOCUMENT_KIND_REGISTRY]


def document_kind_var_groups(key):
    """Nombres de grupos de variables que expone un DocumentKind (para el catálogo)."""
    entry = _DOCUMENT_KIND_BY_KEY.get(key)
    return entry['var_groups'] if entry else ()


TEMPLATE_STAGES = ('diseno', 'legalizacion', 'entrega', 'posventa')

TEMPLATE_SCOPES = ('system', 'org')
TEMPLATE_STATUSES = ('draft', 'published', 'archived')
DOCUMENT_STATUSES = ('generated', 'failed')


class ReportTemplate(BaseModel):
    """Plantilla de documento. org_id NULL + scope 'system' => banco oficial (solo lectura)."""

    __tablename__ = 'report_templates'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), index=True)
    scope = db.Column(db.String(10), nullable=False, default='org')
    kind = db.Column(db.String(40), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), default='')
    country = db.Column(db.String(80))
    region = db.Column(db.String(120))
    locale = db.Column(db.String(10))
    currency = db.Column(db.String(3))
    required_by = db.Column(db.String(120))
    stage = db.Column(db.String(20))
    thumbnail_path = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default='draft')
    is_official = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    versions = db.relationship(
        'TemplateVersion',
        backref='template',
        cascade='all, delete-orphan',
        order_by='TemplateVersion.version.desc()',
    )

    @property
    def is_system(self):
        return self.org_id is None and self.scope == 'system'

    @property
    def latest_version(self):
        return self.versions[0] if self.versions else None

    @property
    def published_version(self):
        for v in self.versions:
            if v.published_at is not None:
                return v
        return None

    @property
    def presentation(self):
        """Jurisdicción efectiva {locale, currency, page_size}: país + overrides explícitos."""
        from app.services.template_engine.jurisdiction import resolve_jurisdiction
        return resolve_jurisdiction(self.country, self.locale, self.currency)

    def to_dict(self, with_content=False):
        latest = self.latest_version
        data = {
            'id': self.id,
            'org_id': self.org_id,
            'scope': self.scope,
            'kind': self.kind,
            'name': self.name,
            'description': self.description or '',
            'country': self.country,
            'region': self.region,
            'locale': self.locale,
            'currency': self.currency,
            'required_by': self.required_by,
            'stage': self.stage,
            'thumbnail_path': self.thumbnail_path,
            'status': self.status,
            'is_official': self.is_official,
            'is_system': self.is_system,
            'created_by': self.created_by,
            'latest_version': latest.version if latest else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if with_content and latest:
            data['content'] = latest.content
        return data

    def __repr__(self):
        scope = 'system' if self.is_system else f'org {self.org_id}'
        return f'<ReportTemplate {self.name} ({self.kind}/{scope})>'


class TemplateVersion(BaseModel):
    """Una versión inmutable del contenido de una plantilla.

    `content` es una lista ordenada de secciones {id, type, title, body}, donde `body` lleva
    texto con expresiones embebidas `{{ ... }}`. Se persiste como JSON en TEXT.
    """

    __tablename__ = 'template_versions'
    __table_args__ = (
        db.UniqueConstraint('template_id', 'version', name='uq_template_version'),
    )

    template_id = db.Column(
        db.Integer, db.ForeignKey('report_templates.id'), nullable=False, index=True
    )
    version = db.Column(db.Integer, nullable=False, default=1)
    _content = db.Column('content', db.Text, nullable=False, default='[]')
    changelog = db.Column(db.String(500), default='')
    published_at = db.Column(db.DateTime, nullable=True)

    @property
    def content(self):
        if not self._content:
            return []
        try:
            return json.loads(self._content)
        except (ValueError, TypeError):
            return []

    @content.setter
    def content(self, value):
        self._content = json.dumps(value if value is not None else [])

    def to_dict(self):
        return {
            'id': self.id,
            'template_id': self.template_id,
            'version': self.version,
            'content': self.content,
            'changelog': self.changelog or '',
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<TemplateVersion t{self.template_id} v{self.version}>'


class TemplateCategory(BaseModel):
    """Categoría plana de la biblioteca de una organización (1:n, sin subniveles)."""

    __tablename__ = 'template_categories'
    __table_args__ = (
        db.UniqueConstraint('org_id', 'name', name='uq_template_category_org_name'),
    )

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'org_id': self.org_id, 'name': self.name}

    def __repr__(self):
        return f'<TemplateCategory {self.name} (org {self.org_id})>'


class Label(BaseModel):
    """Etiqueta de la organización, asignable a instalaciones (n:n)."""

    __tablename__ = 'template_labels'
    __table_args__ = (
        db.UniqueConstraint('org_id', 'name', name='uq_template_label_org_name'),
    )

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'org_id': self.org_id, 'name': self.name}

    def __repr__(self):
        return f'<Label {self.name} (org {self.org_id})>'


class TemplateInstallation(BaseModel):
    """Entrada de la biblioteca de una organización: una plantilla seleccionada."""

    __tablename__ = 'template_installations'
    __table_args__ = (
        db.UniqueConstraint('org_id', 'template_id', name='uq_installation_org_template'),
    )

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    template_id = db.Column(
        db.Integer, db.ForeignKey('report_templates.id'), nullable=False, index=True
    )
    is_favorite = db.Column(db.Boolean, nullable=False, default=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey('template_categories.id'), nullable=True, index=True
    )
    added_at = db.Column(db.DateTime, nullable=True)

    template = db.relationship('ReportTemplate')
    category = db.relationship('TemplateCategory')
    labels = db.relationship(
        'Label', secondary='installation_labels', lazy='joined'
    )

    def to_dict(self, with_template=True):
        data = {
            'id': self.id,
            'org_id': self.org_id,
            'template_id': self.template_id,
            'is_favorite': self.is_favorite,
            'category_id': self.category_id,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'labels': [l.to_dict() for l in self.labels],
        }
        if with_template and self.template is not None:
            data['template'] = self.template.to_dict()
        return data

    def __repr__(self):
        return f'<TemplateInstallation org{self.org_id} -> t{self.template_id}>'


class InstallationLabel(BaseModel):
    """Tabla puente n:n entre instalaciones y etiquetas."""

    __tablename__ = 'installation_labels'
    __table_args__ = (
        db.UniqueConstraint(
            'installation_id', 'label_id', name='uq_installation_label'
        ),
    )

    installation_id = db.Column(
        db.Integer, db.ForeignKey('template_installations.id'), nullable=False, index=True
    )
    label_id = db.Column(
        db.Integer, db.ForeignKey('template_labels.id'), nullable=False, index=True
    )


class GeneratedDocument(BaseModel):
    """PDF generado desde una plantilla (versión fijada) y un proyecto.

    Org-scoped. `template_version_id` fija la versión exacta usada para que el documento sea
    reproducible y trazable aunque la plantilla evolucione. `pdf_path` es la ruta del artefacto
    (relativa a `instance_path`); `pdf_sha256`/`pdf_size_bytes` son el snapshot de integridad.
    """

    __tablename__ = 'generated_documents'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False, index=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True
    )
    template_id = db.Column(
        db.Integer, db.ForeignKey('report_templates.id'), nullable=False, index=True
    )
    template_version_id = db.Column(
        db.Integer, db.ForeignKey('template_versions.id'), nullable=False, index=True
    )
    kind = db.Column(db.String(40), nullable=False, index=True)
    pdf_path = db.Column(db.String(500), nullable=False)
    pdf_sha256 = db.Column(db.String(64), nullable=False)
    pdf_size_bytes = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='generated')
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    generated_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship('Project')
    template = db.relationship('ReportTemplate')
    template_version = db.relationship('TemplateVersion')
    generated_by_user = db.relationship('User', foreign_keys=[generated_by])

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'project_id': self.project_id,
            'template_id': self.template_id,
            'template_version_id': self.template_version_id,
            'template_version': self.template_version.version if self.template_version else None,
            'template_name': self.template.name if self.template else None,
            'kind': self.kind,
            'pdf_sha256': self.pdf_sha256,
            'pdf_size_bytes': self.pdf_size_bytes,
            'status': self.status,
            'generated_by': self.generated_by,
            'generated_by_name': (
                self.generated_by_user.full_name if self.generated_by_user else None
            ),
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<GeneratedDocument t{self.template_id}/v{self.template_version_id} p{self.project_id}>'
