"""Comandos de línea para los scrapers de catálogos.

Uso: `flask scrape list` · `flask scrape run fronius [--dry-run]`.
"""

import click
from flask.cli import AppGroup

from app.scrapers.registry import available
from app.scrapers.service import ScraperService

scrape_cli = AppGroup('scrape', help='Scrapers de catálogos de marcas.')


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
               f"omitidos={len(report['skipped'])} errores={len(report['errors'])}")
    for d in report['created'] + report['updated']:
        falta = ', '.join(d.get('parcial_sin') or []) or 'completo'
        click.echo(f"   ✓ {d.get('nombre')}  [{d['id']}]  (sin: {falta})")
    for s in report['skipped']:
        click.echo(f"   ⤫ {s['id']}: {s['reason']}")
    for e in report['errors']:
        click.echo(f"   ! {e['ref']}: {e['error']}")


def register_cli(app):
    app.cli.add_command(scrape_cli)
