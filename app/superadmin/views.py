"""Vistas server-rendered del portal de superadmin."""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort, session)

from app.extensions import db, limiter
from app import mfa
from app.security import current_user, login_user, logout_user
from app.models.user import User
from app.models.organization import Organization
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.support_ticket import SupportTicket, SupportTicketMessage, TICKET_STATUSES
from app.models.superadmin_audit import SuperadminAudit
from app.superadmin.guards import (require_superadmin, is_superadmin, log_action,
                                   client_ip, set_pending_mfa, clear_pending_mfa,
                                   pending_mfa_user)
from app.superadmin import metrics, migrations_ctl, catalog_admin
from app.services.catalog_service import CatalogService

_MFA_ISSUER = 'Sunalyze Superadmin'

superadmin_bp = Blueprint('superadmin', __name__, template_folder='templates')

_KIND = {'panel': Panel, 'inverter': Inverter}


@superadmin_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if is_superadmin():
        return redirect(url_for('superadmin.index'))
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_superadmin:
            set_pending_mfa(user)
            if user.mfa_enabled:
                return redirect(url_for('superadmin.mfa_challenge'))
            return redirect(url_for('superadmin.mfa_setup'))
        flash('Credenciales inválidas o sin acceso de superadmin.', 'error')
    return render_template('superadmin/login.html')


def _finish_login(user):
    clear_pending_mfa()
    login_user(user)
    target = request.args.get('next') or url_for('superadmin.index')
    return redirect(target)


@superadmin_bp.route('/mfa/setup', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def mfa_setup():
    """Enrolamiento forzado: genera secreto, lo muestra y exige confirmar un código."""
    user = pending_mfa_user()
    if user is None:
        return redirect(url_for('superadmin.login'))
    if user.mfa_enabled:
        return redirect(url_for('superadmin.mfa_challenge'))
    secret = session.get('mfa_setup_secret')
    if not secret:
        secret = mfa.generate_secret()
        session['mfa_setup_secret'] = secret
    if request.method == 'POST':
        code = request.form.get('code') or ''
        if mfa.verify_totp(secret, code):
            codes = user.enable_mfa(secret)
            db.session.commit()
            session.pop('mfa_setup_secret', None)
            log_action('mfa.enable', target=f'user:{user.id}', detail=user.email, actor=user)
            _finish_login(user)
            return render_template('superadmin/mfa_codes.html', codes=codes)
        flash('Código inválido. Reescanea o reintenta.', 'error')
    uri = mfa.provisioning_uri(secret, user.email, _MFA_ISSUER)
    return render_template('superadmin/mfa_setup.html', secret=secret, uri=uri)


@superadmin_bp.route('/mfa/challenge', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def mfa_challenge():
    """Segundo factor en el login: TOTP de 6 dígitos o un código de recuperación."""
    user = pending_mfa_user()
    if user is None:
        return redirect(url_for('superadmin.login'))
    if not user.mfa_enabled:
        return redirect(url_for('superadmin.mfa_setup'))
    if request.method == 'POST':
        code = (request.form.get('code') or '').strip()
        if user.verify_totp(code):
            log_action('mfa.login', target=f'user:{user.id}', detail=user.email, actor=user)
            return _finish_login(user)
        if user.consume_recovery_code(code):
            db.session.commit()
            log_action('mfa.recovery_used', target=f'user:{user.id}',
                       detail=f'{user.recovery_codes_remaining} restantes', actor=user)
            return _finish_login(user)
        flash('Código inválido.', 'error')
    return render_template('superadmin/mfa_challenge.html')


@superadmin_bp.route('/logout', methods=['POST'])
def logout():
    clear_pending_mfa()
    session.pop('mfa_setup_secret', None)
    logout_user()
    return redirect(url_for('superadmin.login'))


@superadmin_bp.route('/')
@require_superadmin
def index():
    return render_template('superadmin/dashboard.html', m=metrics.dashboard())


@superadmin_bp.route('/equipment/review')
@require_superadmin
def equipment_review():
    panels = Panel.query.filter(Panel.needs_review.is_(True)).all()
    inverters = Inverter.query.filter(Inverter.needs_review.is_(True)).all()
    return render_template('superadmin/equipment.html', panels=panels, inverters=inverters)


@superadmin_bp.route('/equipment/<kind>/<int:item_id>/approve', methods=['POST'])
@require_superadmin
def equipment_approve(kind, item_id):
    model = _KIND.get(kind)
    if not model:
        abort(404)
    item = model.query.get_or_404(item_id)
    item.needs_review = False
    item.review_notes = None
    db.session.commit()
    log_action('equipment.approve', target=f'{kind}:{item_id}', detail=item.nombre)
    flash(f'«{item.nombre}» aprobado.', 'ok')
    return redirect(url_for('superadmin.equipment_review'))


@superadmin_bp.route('/catalogs')
@require_superadmin
def catalogs_view():
    return render_template('superadmin/catalogs.html', catalogs=catalog_admin.list_all())


@superadmin_bp.route('/catalogs/<int:catalog_id>')
@require_superadmin
def catalog_detail(catalog_id):
    catalog = catalog_admin.get(catalog_id)
    if not catalog:
        abort(404)
    others = [c for c in catalog_admin.list_all() if c['id'] != catalog_id and c['is_active']]
    return render_template('superadmin/catalog_detail.html', c=catalog,
                           counts=CatalogService._counts(catalog_id), targets=others)


@superadmin_bp.route('/catalogs', methods=['POST'])
@require_superadmin
def catalog_create():
    nombre = (request.form.get('nombre') or '').strip()
    if not nombre:
        flash('El nombre es obligatorio.', 'error')
        return redirect(url_for('superadmin.catalogs_view'))
    c = catalog_admin.create(nombre, request.form.get('descripcion'),
                             request.form.get('scraper_name'),
                             request.form.get('is_official') == 'on')
    log_action('catalog.create', target=f'catalog:{c.id}', detail=c.nombre)
    flash(f'Catálogo «{c.nombre}» creado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/edit', methods=['POST'])
@require_superadmin
def catalog_edit(catalog_id):
    c = catalog_admin.edit(catalog_id, request.form.get('nombre') or '',
                           request.form.get('descripcion'), request.form.get('scraper_name'))
    if not c:
        abort(404)
    log_action('catalog.edit', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash('Catálogo actualizado.', 'ok')
    return redirect(url_for('superadmin.catalog_detail', catalog_id=catalog_id))


@superadmin_bp.route('/catalogs/<int:catalog_id>/activate', methods=['POST'])
@require_superadmin
def catalog_activate(catalog_id):
    c = catalog_admin.set_active(catalog_id, True)
    if not c:
        abort(404)
    log_action('catalog.activate', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» activado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/deactivate', methods=['POST'])
@require_superadmin
def catalog_deactivate(catalog_id):
    c = catalog_admin.set_active(catalog_id, False)
    if not c:
        abort(404)
    log_action('catalog.deactivate', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» desactivado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/delete', methods=['POST'])
@require_superadmin
def catalog_delete(catalog_id):
    c = catalog_admin.delete(catalog_id)
    if not c:
        abort(404)
    log_action('catalog.delete', target=f'catalog:{catalog_id}', detail=c.nombre)
    flash(f'«{c.nombre}» eliminado.', 'ok')
    return redirect(url_for('superadmin.catalogs_view'))


@superadmin_bp.route('/catalogs/<int:catalog_id>/merge')
@require_superadmin
def catalog_merge_preview(catalog_id):
    target_id = request.args.get('target', type=int)
    if not target_id:
        flash('Selecciona un catálogo destino.', 'error')
        return redirect(url_for('superadmin.catalog_detail', catalog_id=catalog_id))
    preview = catalog_admin.merge_preview(catalog_id, target_id)
    return render_template('superadmin/catalog_merge.html', preview=preview,
                           src_id=catalog_id, target_id=target_id)


@superadmin_bp.route('/catalogs/<int:catalog_id>/merge', methods=['POST'])
@require_superadmin
def catalog_merge_apply(catalog_id):
    target_id = request.form.get('target', type=int)
    decisions = {k[len('decision:'):]: v for k, v in request.form.items() if k.startswith('decision:')}
    res = catalog_admin.merge_apply(catalog_id, target_id, decisions)
    log_action('catalog.merge', target=f'catalog:{catalog_id}->{target_id}', detail=str(res))
    flash(f"Merge: {res['moved']} movidos, {res['dropped']} descartados, {res['replaced']} reemplazados.", 'ok')
    return redirect(url_for('superadmin.catalog_detail', catalog_id=target_id))


@superadmin_bp.route('/migrations')
@require_superadmin
def migrations_view():
    return render_template('superadmin/migrations.html',
                           status=migrations_ctl.status(), history=migrations_ctl.history())


@superadmin_bp.route('/migrations/upgrade', methods=['POST'])
@require_superadmin
def migrations_upgrade():
    if request.form.get('confirm') != 'upgrade':
        flash('Debes confirmar la operación.', 'error')
        return redirect(url_for('superadmin.migrations_view'))
    try:
        before, after = migrations_ctl.do_upgrade()
    except Exception as exc:
        log_action('migration.upgrade.error', detail=str(exc))
        flash(f'Falló la migración: {exc}', 'error')
        return redirect(url_for('superadmin.migrations_view'))
    log_action('migration.upgrade', target=f'{before} -> {after}')
    if before == after:
        flash('Ya estaba al día; nada que aplicar.', 'ok')
    else:
        flash(f'Migrado {before or "(base)"} → {after}.', 'ok')
    return redirect(url_for('superadmin.migrations_view'))


@superadmin_bp.route('/users')
@require_superadmin
def users_view():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('superadmin/users.html', users=users)


@superadmin_bp.route('/users/<int:user_id>/superadmin', methods=['POST'])
@require_superadmin
def users_toggle_superadmin(user_id):
    user = User.query.get_or_404(user_id)
    me = current_user()
    if user.id == me.id:
        flash('No puedes cambiar tu propio acceso de superadmin.', 'error')
        return redirect(url_for('superadmin.users_view'))
    user.is_superadmin = not user.is_superadmin
    db.session.commit()
    log_action('user.superadmin.' + ('grant' if user.is_superadmin else 'revoke'),
               target=f'user:{user.id}', detail=user.email)
    flash(f'{user.email}: superadmin = {user.is_superadmin}.', 'ok')
    return redirect(url_for('superadmin.users_view'))


@superadmin_bp.route('/orgs')
@require_superadmin
def orgs_view():
    orgs = Organization.query.order_by(Organization.created_at.desc()).all()
    return render_template('superadmin/orgs.html', orgs=orgs)


@superadmin_bp.route('/tickets')
@require_superadmin
def tickets_view():
    status = request.args.get('status')
    query = SupportTicket.query
    if status in TICKET_STATUSES:
        query = query.filter_by(status=status)
    tickets = query.order_by(SupportTicket.updated_at.desc()).all()
    return render_template('superadmin/tickets.html', tickets=tickets,
                           statuses=TICKET_STATUSES, active=status)


@superadmin_bp.route('/tickets/<int:ticket_id>')
@require_superadmin
def ticket_detail(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    return render_template('superadmin/ticket_detail.html', t=ticket, statuses=TICKET_STATUSES)


@superadmin_bp.route('/tickets/<int:ticket_id>/reply', methods=['POST'])
@require_superadmin
def ticket_reply(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    body = (request.form.get('body') or '').strip()
    if not body:
        flash('El mensaje no puede estar vacío.', 'error')
        return redirect(url_for('superadmin.ticket_detail', ticket_id=ticket_id))
    msg = SupportTicketMessage(ticket_id=ticket.id, body=body,
                               author=current_user().email, is_staff=True)
    if ticket.status == 'open':
        ticket.status = 'pending'
    db.session.add(msg)
    db.session.commit()
    log_action('ticket.reply', target=f'ticket:{ticket_id}')
    return redirect(url_for('superadmin.ticket_detail', ticket_id=ticket_id))


@superadmin_bp.route('/tickets/<int:ticket_id>/status', methods=['POST'])
@require_superadmin
def ticket_status(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    new_status = request.form.get('status')
    if new_status not in TICKET_STATUSES:
        abort(400)
    ticket.status = new_status
    db.session.commit()
    log_action('ticket.status', target=f'ticket:{ticket_id}', detail=new_status)
    flash(f'Estado del ticket #{ticket_id}: {new_status}.', 'ok')
    return redirect(url_for('superadmin.ticket_detail', ticket_id=ticket_id))


@superadmin_bp.route('/audit')
@require_superadmin
def audit_view():
    entries = SuperadminAudit.query.order_by(SuperadminAudit.created_at.desc()).limit(200).all()
    return render_template('superadmin/audit.html', entries=entries)
