"""Agregados para el dashboard de métricas del superadmin."""

from sqlalchemy import func

from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.project import Project
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.support_ticket import SupportTicket


def _count(model):
    return db.session.query(func.count(model.id)).scalar() or 0


def _review_count(model):
    return db.session.query(func.count(model.id)).filter(model.needs_review.is_(True)).scalar() or 0


def dashboard():
    by_plan = dict(db.session.query(Organization.plan, func.count(Organization.id))
                   .group_by(Organization.plan).all())
    by_status = dict(db.session.query(SupportTicket.status, func.count(SupportTicket.id))
                     .group_by(SupportTicket.status).all())
    return {
        'users': _count(User),
        'superadmins': db.session.query(func.count(User.id)).filter(User.is_superadmin.is_(True)).scalar() or 0,
        'orgs': _count(Organization),
        'orgs_by_plan': by_plan,
        'projects': _count(Project),
        'panels': _count(Panel),
        'inverters': _count(Inverter),
        'review_pending': _review_count(Panel) + _review_count(Inverter),
        'tickets_open': by_status.get('open', 0),
        'tickets_pending': by_status.get('pending', 0),
        'tickets_total': _count(SupportTicket),
    }
