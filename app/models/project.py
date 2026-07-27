
import json

from app import db
from .database import BaseModel, SoftDeleteMixin

ESTADOS = ('borrador', 'en_revision', 'presentado', 'aprobado', 'rechazado')

_UNSET = object()


class Project(BaseModel, SoftDeleteMixin):
    __tablename__ = 'projects'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True)

    serial_seq = db.Column(db.Integer, nullable=True)

    cliente = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(255))
    localidad = db.Column(db.String(120))
    estado = db.Column(db.String(20), nullable=False, default='borrador')

    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    necesidad = db.Column(db.Float)
    autoconsumo = db.Column(db.Float)
    coplanar = db.Column(db.Boolean, default=False)
    inclinacion = db.Column(db.Float)
    azimut = db.Column(db.Float)

    panel_id = db.Column(db.Integer, db.ForeignKey('panels.id'))
    inverter_id = db.Column(db.Integer, db.ForeignKey('inverters.id'))
    battery_id = db.Column(db.Integer, db.ForeignKey('batteries.id'))
    battery_quantity = db.Column(db.Integer, default=1)

    referencia_catastral = db.Column(db.String(40))
    cups = db.Column(db.String(40))
    compania = db.Column(db.String(80))
    potencia_contratada = db.Column(db.Float)
    tipo_voltaje = db.Column(db.String(20))

    ccaa = db.Column(db.String(40))
    expediente_numero = db.Column(db.String(60))
    expediente_fecha = db.Column(db.Date)

    _resultados = db.Column('resultados', db.Text)

    panel = db.relationship('Panel', foreign_keys=[panel_id])
    inverter = db.relationship('Inverter', foreign_keys=[inverter_id])
    battery = db.relationship('Battery', foreign_keys=[battery_id])

    signatures = db.relationship(
        'MemoriaSignature',
        backref='project',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='MemoriaSignature.created_at.desc()',
    )
    events = db.relationship(
        'ProjectEvent',
        backref='project',
        cascade='all, delete-orphan',
        passive_deletes=True,
        order_by='ProjectEvent.created_at.desc()',
    )

    @classmethod
    def next_serial_seq(cls, org_id):
        current = (
            db.session.query(db.func.max(cls.serial_seq))
            .filter(cls.org_id == org_id)
            .scalar()
        )
        return (current or 0) + 1

    def formatted_serial(self, prefix):
        if self.serial_seq is None:
            return None
        padded = f'{self.serial_seq:04d}'
        clean_prefix = (prefix or '').strip()
        if clean_prefix:
            return f'{clean_prefix}-{padded}'
        return padded

    @property
    def current_signature(self):
        for signature in self.signatures:
            if signature.is_current:
                return signature
        return None

    @property
    def resultados(self):
        if not self._resultados:
            return None
        try:
            return json.loads(self._resultados)
        except (ValueError, TypeError):
            return None

    @resultados.setter
    def resultados(self, value):
        self._resultados = json.dumps(value) if value is not None else None

    @property
    def kwp(self):
        data = self.resultados
        if data and data.get('total_field_power') is not None:
            return round(float(data['total_field_power']), 2)
        return None

    @property
    def n_paneles(self):
        data = self.resultados
        if data and data.get('cell_amount') is not None:
            import math
            return math.ceil(float(data['cell_amount']))
        return None

    def to_dict(self, prefix=_UNSET):
        if prefix is _UNSET:
            from app.services.org_service import OrgService
            prefix = OrgService.get_branding(self.org_id).get('project_prefix')
        return {
            'id': self.id,
            'org_id': self.org_id,
            'serial_seq': self.serial_seq,
            'serial': self.formatted_serial(prefix),
            'cliente': self.cliente,
            'direccion': self.direccion,
            'localidad': self.localidad,
            'estado': self.estado,
            'latitud': self.latitud,
            'longitud': self.longitud,
            'necesidad': self.necesidad,
            'autoconsumo': self.autoconsumo,
            'coplanar': self.coplanar,
            'inclinacion': self.inclinacion,
            'azimut': self.azimut,
            'panel_id': self.panel_id,
            'inverter_id': self.inverter_id,
            'battery_id': self.battery_id,
            'battery_quantity': self.battery_quantity,
            'panel_nombre': self.panel.nombre if self.panel else None,
            'inverter_nombre': self.inverter.nombre if self.inverter else None,
            'battery_nombre': self.battery.nombre if self.battery else None,
            'referencia_catastral': self.referencia_catastral,
            'cups': self.cups,
            'compania': self.compania,
            'potencia_contratada': self.potencia_contratada,
            'tipo_voltaje': self.tipo_voltaje,
            'ccaa': self.ccaa,
            'expediente_numero': self.expediente_numero,
            'expediente_fecha': self.expediente_fecha.isoformat() if self.expediente_fecha else None,
            'resultados': self.resultados,
            'kwp': self.kwp,
            'n_paneles': self.n_paneles,
            'memoria_firmada': self.current_signature is not None,
            'firma': self.current_signature.to_dict() if self.current_signature else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }

    def __repr__(self):
        return f'<Project {self.cliente} ({self.estado})>'
