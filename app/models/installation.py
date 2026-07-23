
from app import db
from .database import BaseModel

INSTALLATION_STATUSES = ('operativa', 'incidencia', 'mantenimiento', 'baja')

MAINTENANCE_KINDS = ('preventivo', 'correctivo')
MAINTENANCE_STATUSES = ('programada', 'realizada', 'cancelada')

INCIDENT_SEVERITIES = ('baja', 'media', 'alta', 'critica')
INCIDENT_STATUSES = ('abierta', 'en_proceso', 'resuelta')


class Installation(BaseModel):
    __tablename__ = 'installations'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), index=True, nullable=False, unique=True)

    status = db.Column(db.String(20), nullable=False, default='operativa')
    commissioned_at = db.Column(db.Date)
    warranty_until = db.Column(db.Date)
    expected_annual_kwh = db.Column(db.Float)
    notes = db.Column(db.Text)

    project = db.relationship('Project')
    maintenance_visits = db.relationship(
        'MaintenanceVisit', back_populates='installation',
        cascade='all, delete-orphan', passive_deletes=True,
        order_by='MaintenanceVisit.scheduled_at.desc()',
    )
    incidents = db.relationship(
        'Incident', back_populates='installation',
        cascade='all, delete-orphan', passive_deletes=True,
        order_by='Incident.opened_at.desc()',
    )
    readings = db.relationship(
        'ProductionReading', back_populates='installation',
        cascade='all, delete-orphan', passive_deletes=True,
        order_by='ProductionReading.period',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'project_id': self.project_id,
            'cliente': self.project.cliente if self.project else None,
            'status': self.status,
            'commissioned_at': self.commissioned_at.isoformat() if self.commissioned_at else None,
            'warranty_until': self.warranty_until.isoformat() if self.warranty_until else None,
            'expected_annual_kwh': self.expected_annual_kwh,
            'notes': self.notes,
            'maintenance_count': len(self.maintenance_visits),
            'incident_count': len(self.incidents),
            'reading_count': len(self.readings),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f'<Installation p{self.project_id} ({self.status})>'


class MaintenanceVisit(BaseModel):
    __tablename__ = 'maintenance_visits'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    installation_id = db.Column(db.Integer, db.ForeignKey('installations.id', ondelete='CASCADE'), index=True, nullable=False)

    kind = db.Column(db.String(20), nullable=False, default='preventivo')
    status = db.Column(db.String(20), nullable=False, default='programada')
    scheduled_at = db.Column(db.Date)
    done_at = db.Column(db.Date)
    technician = db.Column(db.String(150))
    notes = db.Column(db.Text)

    installation = db.relationship('Installation', back_populates='maintenance_visits')

    def to_dict(self):
        return {
            'id': self.id,
            'installation_id': self.installation_id,
            'kind': self.kind,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'done_at': self.done_at.isoformat() if self.done_at else None,
            'technician': self.technician,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Incident(BaseModel):
    __tablename__ = 'installation_incidents'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    installation_id = db.Column(db.Integer, db.ForeignKey('installations.id', ondelete='CASCADE'), index=True, nullable=False)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), nullable=False, default='media')
    status = db.Column(db.String(20), nullable=False, default='abierta')
    opened_at = db.Column(db.Date)
    resolved_at = db.Column(db.Date)

    installation = db.relationship('Installation', back_populates='incidents')

    def to_dict(self):
        return {
            'id': self.id,
            'installation_id': self.installation_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ProductionReading(BaseModel):
    __tablename__ = 'production_readings'

    org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), index=True, nullable=False)
    installation_id = db.Column(db.Integer, db.ForeignKey('installations.id', ondelete='CASCADE'), index=True, nullable=False)

    period = db.Column(db.String(20), nullable=False)
    actual_kwh = db.Column(db.Float, nullable=False)

    installation = db.relationship('Installation', back_populates='readings')

    def to_dict(self):
        return {
            'id': self.id,
            'installation_id': self.installation_id,
            'period': self.period,
            'actual_kwh': self.actual_kwh,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
