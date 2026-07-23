"""Comandos de línea: portal de superadmin y scrapers de catálogos.

- `flask superadmin grant|revoke|mfa-reset|list <email>` — bootstrap del portal.
- `flask scrape list` · `flask scrape run <brand> [--dry-run]` — scrapers de marcas.
- `flask flags seed` — asegura los feature flags por defecto.
- `flask docs seed` — siembra el banco oficial de tipos de documento (España).
- `flask seed demo` — cuenta de prueba superadmin + dataset de demo (idempotente).
"""

import os

import click
from flask import current_app
from flask.cli import AppGroup

from app.extensions import db
from app.models.user import User
from app.scrapers.registry import available
from app.scrapers.service import ScraperService

superadmin_cli = AppGroup('superadmin', help='Gestión del portal de superadmin.')
scrape_cli = AppGroup('scrape', help='Scrapers de catálogos de marcas.')
flags_cli = AppGroup('flags', help='Gestión de feature flags.')
docs_cli = AppGroup('docs', help='Banco oficial de tipos de documento.')
seed_cli = AppGroup('seed', help='Datos de prueba para desarrollo local.')


@seed_cli.command('demo')
def seed_demo():
    """Crea la cuenta de prueba (superadmin) y un dataset de demo completo. Idempotente."""
    from app.services.demo_seed import DemoSeeder, DEMO_EMAIL, DEMO_PASSWORD
    if current_app.config.get('IS_PRODUCTION') and os.environ.get('ALLOW_SEED_DEMO') != '1':
        click.echo('Aviso: entorno marcado como producción. Si es un despliegue real NO sigas; '
                   'para un entorno local con Docker, reintenta con ALLOW_SEED_DEMO=1.')
        raise click.Abort()
    report = DemoSeeder.seed()
    click.echo(f"Dataset: {report['dataset']}")
    click.echo(f"Plantillas oficiales: {report['documentos']['created']} creadas, "
               f"{report['documentos']['skipped']} ya existían.")
    click.echo(f'Cuenta de prueba lista: {DEMO_EMAIL} / {DEMO_PASSWORD} (superadmin).')


def _find(email):
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        raise click.ClickException(f'No existe el usuario «{email}».')
    return user


@superadmin_cli.command('grant')
@click.argument('email')
def grant(email):
    user = _find(email)
    user.is_superadmin = True
    db.session.commit()
    click.echo(f'{user.email} ahora es superadmin.')


@superadmin_cli.command('revoke')
@click.argument('email')
def revoke(email):
    user = _find(email)
    user.is_superadmin = False
    db.session.commit()
    click.echo(f'{user.email} ya no es superadmin.')


@superadmin_cli.command('mfa-reset')
@click.argument('email')
def mfa_reset(email):
    """Desactiva el MFA de un superadmin (recuperación ante pérdida del factor).

    El usuario será forzado a reenrolar en su próximo login."""
    user = _find(email)
    user.mfa_enabled = False
    user.mfa_secret = None
    user.mfa_recovery_codes = None
    db.session.commit()
    click.echo(f'MFA reiniciado para {user.email}; deberá reenrolar al entrar.')


@superadmin_cli.command('list')
def list_superadmins():
    users = User.query.filter_by(is_superadmin=True).all()
    if not users:
        click.echo('(no hay superadmins)')
    for u in users:
        click.echo(f'  {u.email}')


@scrape_cli.command('list')
def list_brands():
    click.echo('Marcas con scraper: ' + (', '.join(available()) or '(ninguna)'))


@scrape_cli.command('run')
@click.argument('brand')
@click.option('--dry-run', is_flag=True, help='No escribe; reporta qué haría.')
def run(brand, dry_run):
    try:
        report = ScraperService.run(brand, dry_run=dry_run)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"[{report['brand']}] dry_run={report['dry_run']}  "
               f"creados={len(report['created'])} actualizados={len(report['updated'])} "
               f"a_revisar={len(report['review'])} bloqueados={len(report['blocked'])} "
               f"omitidos={len(report['skipped'])} errores={len(report['errors'])}")
    for d in report['created'] + report['updated']:
        falta = ', '.join(d.get('parcial_sin') or []) or 'completo'
        marca = ' ⚑ revisión' if d.get('needs_review') else ''
        click.echo(f"   ✓ {d.get('nombre')}  [{d['id']}]  (sin: {falta}){marca}")
    for r in report['review']:
        click.echo(f"   ⚑ {r['id']}: {r['reason']}")
    for b in report['blocked']:
        click.echo(f"   ⛔ {b['id']}: {b['reason']}")
    for s in report['skipped']:
        click.echo(f"   ⤫ {s['id']}: {s['reason']}")
    for e in report['errors']:
        click.echo(f"   ! {e['ref']}: {e['error']}")


@flags_cli.command('seed')
def seed_flags():
    from app.services.flag_service import FlagService
    created = FlagService.ensure_defaults()
    click.echo(f'Flags por defecto asegurados ({created} creados).')


@docs_cli.command('seed')
def seed_docs():
    """Siembra el banco oficial de tipos de documento (España). Idempotente."""
    from app.services.document_bank import DocumentBankSeeder
    report = DocumentBankSeeder.seed()
    click.echo(
        f"Banco oficial de documentos ES: {report['created']} creados, "
        f"{report['skipped']} ya existían."
    )


_HTTP_METHODS = ('GET', 'POST', 'PATCH', 'PUT', 'DELETE')


def _first_docline(view):
    doc = (view.__doc__ or '').strip()
    return doc.splitlines()[0].strip() if doc else ''


def _api_rows():
    rows = []
    for rule in current_app.url_map.iter_rules():
        if not rule.rule.startswith('/api'):
            continue
        methods = sorted(
            (rule.methods or set()) & set(_HTTP_METHODS),
            key=_HTTP_METHODS.index,
        )
        view = current_app.view_functions.get(rule.endpoint)
        blueprint = rule.endpoint.rsplit('.', 1)[0] if '.' in rule.endpoint else '(app)'
        rows.append({
            'blueprint': blueprint,
            'methods': ', '.join(methods),
            'rule': rule.rule,
            'endpoint': rule.endpoint,
            'summary': _first_docline(view) if view else '',
        })
    return rows


def _render_api_map(rows):
    total = len(rows)
    by_blueprint = {}
    for row in rows:
        by_blueprint.setdefault(row['blueprint'], []).append(row)

    lines = [
        '# API map',
        '',
        f'Mapa autogenerado por `flask api-map`. Endpoints `/api`: {total}.',
        '',
        'No editar a mano: regenerar con `flask api-map`.',
        '',
    ]
    for blueprint in sorted(by_blueprint):
        entries = sorted(by_blueprint[blueprint], key=lambda r: (r['rule'], r['methods']))
        lines.append(f'## {blueprint}')
        lines.append('')
        lines.append('| Método(s) | Ruta | Endpoint | Resumen |')
        lines.append('| --- | --- | --- | --- |')
        for row in entries:
            summary = row['summary'].replace('|', '\\|')
            lines.append(
                f"| {row['methods']} | `{row['rule']}` | `{row['endpoint']}` | {summary} |"
            )
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


@click.command('api-map')
def api_map():
    """Introspecta el url_map, filtra rutas /api y escribe docs/api-map.md."""
    rows = _api_rows()
    content = _render_api_map(rows)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(root, 'docs', 'api-map.md')
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(content)
    click.echo(f'docs/api-map.md actualizado ({len(rows)} endpoints).')


def register_cli(app):
    app.cli.add_command(superadmin_cli)
    app.cli.add_command(scrape_cli)
    app.cli.add_command(flags_cli)
    app.cli.add_command(docs_cli)
    app.cli.add_command(seed_cli)
    app.cli.add_command(api_map)
