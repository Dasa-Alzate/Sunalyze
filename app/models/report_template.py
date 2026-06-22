"""Modelos del constructor de plantillas de documentos (a nivel de organización).

Patrón system/oficial igual que `Catalog`: una plantilla con `org_id` NULL y `scope='system'`
es del banco oficial (solo lectura); con `org_id` presente pertenece al workspace. La
biblioteca de una organización son sus `TemplateInstallation` (plantillas seleccionadas, con
favorito, categoría y etiquetas). Quitar de la selección borra solo la fila de instalación,
nunca la plantilla system.

`GeneratedDocument` no se modela todavía (nota para futuro; la firma de memoria ya existe).
"""

import json

from app.extensions import db
from .database import BaseModel


class DocumentKind:
    """Tipos de documento soportados. Constantes, no tabla."""

    MEMORIA_CALCULO = 'memoria_calculo'
    DOCUMENTO_LEGAL = 'documento_legal'
    PROPUESTA_COMERCIAL = 'propuesta_comercial'
    ANALISIS_CASO = 'analisis_caso'

    ALL = (MEMORIA_CALCULO, DOCUMENTO_LEGAL, PROPUESTA_COMERCIAL, ANALISIS_CASO)


TEMPLATE_SCOPES = ('system', 'org')
TEMPLATE_STATUSES = ('draft', 'published', 'archived')


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
