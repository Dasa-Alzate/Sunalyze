"""Comandos de línea: portal de superadmin y scrapers de catálogos.

- `flask superadmin grant|revoke|mfa-reset|list <email>` — bootstrap del portal.
- `flask scrape list` · `flask scrape run <brand> [--dry-run]` — scrapers de marcas.
- `flask flags seed` — asegura los feature flags por defecto.
"""

import click
from flask.cli import AppGroup

from app.extensions import db
from app.models.user import User
from app.scrapers.registry import available
from app.scrapers.service import ScraperService

superadmin_cli = AppGroup('superadmin', help='Gestión del portal de superadmin.')
scrape_cli = AppGroup('scrape', help='Scrapers de catálogos de marcas.')
flags_cli = AppGroup('flags', help='Gestión de feature flags.')


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


def register_cli(app):
    app.cli.add_command(superadmin_cli)
    app.cli.add_command(scrape_cli)
    app.cli.add_command(flags_cli)
