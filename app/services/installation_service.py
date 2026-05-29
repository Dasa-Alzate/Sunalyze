"""Dominio de posventa: instalaciones y su seguimiento (sin Flask).

Crea instalaciones desde proyectos aprobados (tomando el baseline de produccion
del dimensionamiento), gestiona el estado operativo y el CRUD de visitas de
mantenimiento, incidencias y lecturas. Devuelve modelos y lanza DomainError.
"""

import logging

from app.extensions import db
from app.models.project import Project
from app.models.installation import (
    Installation, MaintenanceVisit, Incident, ProductionReading,
    INSTALLATION_STATUSES, MAINTENANCE_KINDS, MAINTENANCE_STATUSES,
    INCIDENT_SEVERITIES, INCIDENT_STATUSES,
)
from app.errors import NotFound, ValidationError, Conflict

logger = logging.getLogger(__name__)

APPROVED_ESTADO = 'aprobado'

_VISIT_FIELDS = ('kind', 'status', 'scheduled_at', 'done_at', 'technician', 'notes')
_INCIDENT_FIELDS = ('title', 'description', 'severity', 'status', 'opened_at', 'resolved_at')
_READING_FIELDS = ('period', 'actual_kwh')

_INSTALLATION_EDITABLE = ('commissioned_at', 'warranty_until', 'expected_annual_kwh', 'notes')


def _check_choice(value, allowed, label):
    if value is not None and value not in allowed:
        raise ValidationError(f"{label} invalido. Validos: {', '.join(allowed)}.")


class InstallationService:

    @staticmethod
    def create_from_project(org_id, project_id):
        """Crea la instalacion de un proyecto aprobado, con baseline del analisis.

        Conflict si el proyecto no esta aprobado o si ya tiene instalacion.
        NotFound si el proyecto no existe o es de otra org.
        """
        project = Project.query.get(project_id)
        if not project or project.org_id != org_id:
            raise NotFound('Proyecto no encontrado.')

        if project.estado != APPROVED_ESTADO:
            raise Conflict(
                'Solo se puede crear la instalacion de un proyecto aprobado. '
                f"Estado actual: '{project.estado}'."
            )

        if Installation.query.filter_by(project_id=project.id).first():
            raise Conflict('Este proyecto ya tiene una instalacion.')

        expected = None
        resultados = project.resultados
        if isinstance(resultados, dict) and resultados.get('annual_production') is not None:
            try:
                expected = float(resultados['annual_production'])
            except (TypeError, ValueError):
                expected = None

        installation = Installation(
            org_id=org_id,
            project_id=project.id,
            status='operativa',
            expected_annual_kwh=expected,
        )
        db.session.add(installation)
        db.session.commit()
        logger.info('Instalacion creada desde proyecto p%s (org %s)', project.id, org_id)
        return installation

    @staticmethod
    def set_status(installation, status):
        """Cambia el estado operativo de la instalacion (conjunto abierto)."""
        if status not in INSTALLATION_STATUSES:
            raise ValidationError(
                f"Estado invalido. Validos: {', '.join(INSTALLATION_STATUSES)}."
            )
        installation.status = status
        db.session.commit()
        return installation

    @staticmethod
    def update_installation(installation, data):
        for field in _INSTALLATION_EDITABLE:
            if field in data:
                setattr(installation, field, data[field])
        if 'status' in data:
            _check_choice(data['status'], INSTALLATION_STATUSES, 'Estado')
            installation.status = data['status']
        db.session.commit()
        return installation

    @staticmethod
    def add_visit(installation, data):
        _check_choice(data.get('kind'), MAINTENANCE_KINDS, 'Tipo de visita')
        _check_choice(data.get('status'), MAINTENANCE_STATUSES, 'Estado de visita')
        visit = MaintenanceVisit(org_id=installation.org_id, installation_id=installation.id)
        for field in _VISIT_FIELDS:
            if field in data:
                setattr(visit, field, data[field])
        db.session.add(visit)
        db.session.commit()
        return visit

    @staticmethod
    def update_visit(visit, data):
        _check_choice(data.get('kind'), MAINTENANCE_KINDS, 'Tipo de visita')
        _check_choice(data.get('status'), MAINTENANCE_STATUSES, 'Estado de visita')
        for field in _VISIT_FIELDS:
            if field in data:
                setattr(visit, field, data[field])
        db.session.commit()
        return visit

    @staticmethod
    def add_incident(installation, data):
        if not data.get('title'):
            raise ValidationError('Campo requerido: title.')
        _check_choice(data.get('severity'), INCIDENT_SEVERITIES, 'Severidad')
        _check_choice(data.get('status'), INCIDENT_STATUSES, 'Estado de incidencia')
        incident = Incident(org_id=installation.org_id, installation_id=installation.id)
        for field in _INCIDENT_FIELDS:
            if field in data:
                setattr(incident, field, data[field])
        db.session.add(incident)
        db.session.commit()
        return incident

    @staticmethod
    def update_incident(incident, data):
        _check_choice(data.get('severity'), INCIDENT_SEVERITIES, 'Severidad')
        _check_choice(data.get('status'), INCIDENT_STATUSES, 'Estado de incidencia')
        for field in _INCIDENT_FIELDS:
            if field in data:
                setattr(incident, field, data[field])
        db.session.commit()
        return incident

    @staticmethod
    def add_reading(installation, data):
        if not data.get('period'):
            raise ValidationError('Campo requerido: period.')
        if data.get('actual_kwh') in (None, ''):
            raise ValidationError('Campo requerido: actual_kwh.')
        try:
            actual = float(data['actual_kwh'])
        except (TypeError, ValueError):
            raise ValidationError("El campo 'actual_kwh' debe ser numerico.")
        reading = ProductionReading(
            org_id=installation.org_id, installation_id=installation.id,
            period=str(data['period']), actual_kwh=actual,
        )
        db.session.add(reading)
        db.session.commit()
        return reading

    @staticmethod
    def update_reading(reading, data):
        if 'period' in data:
            if not data['period']:
                raise ValidationError('Campo requerido: period.')
            reading.period = str(data['period'])
        if 'actual_kwh' in data:
            try:
                reading.actual_kwh = float(data['actual_kwh'])
            except (TypeError, ValueError):
                raise ValidationError("El campo 'actual_kwh' debe ser numerico.")
        db.session.commit()
        return reading

    @staticmethod
    def delete(entity):
        db.session.delete(entity)
        db.session.commit()

    @staticmethod
    def performance_summary(installation):
        """Resumen esperado-vs-real a partir de la suma de lecturas manuales.

        El real fiable exige monitorizacion automatica (datalogger / API del
        inversor), deuda futura. v1 suma lecturas manuales: la cifra es
        indicativa y no se normaliza por el periodo realmente cubierto.
        """
        readings = installation.readings
        actual_total = round(sum(r.actual_kwh for r in readings), 2)
        expected = installation.expected_annual_kwh
        ratio = None
        if expected:
            ratio = round(actual_total / expected, 3)
        return {
            'installation_id': installation.id,
            'expected_annual_kwh': expected,
            'actual_total_kwh': actual_total,
            'reading_count': len(readings),
            'ratio': ratio,
            'method': 'manual_readings_v1',
            'method_note': (
                'Suma de lecturas manuales frente al baseline esperado del '
                'dimensionamiento. El real fiable requiere monitorizacion '
                'automatica (datalogger / API del inversor), pendiente. No '
                'normaliza por el periodo realmente cubierto.'
            ),
        }
