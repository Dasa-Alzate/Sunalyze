"""Comandos de línea para operación de plataforma.

Uso: `flask platform grant-admin <email>` / `revoke-admin` / `list-admins`.
Es la vía para gestionar el super-admin sin exponer su concesión por la API.
"""

import click
from flask.cli import AppGroup

from app.extensions import db
from app.models.user import User

platform_cli = AppGroup('platform', help='Operaciones de plataforma (super-admin).')


def _find(email):
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        raise click.ClickException(f'Usuario no encontrado: {email}')
    return user


@platform_cli.command('grant-admin')
@click.argument('email')
def grant_admin(email):
    user = _find(email)
    user.is_platform_admin = True
    db.session.commit()
    click.echo(f'{user.email} es ahora administrador de plataforma.')


@platform_cli.command('revoke-admin')
@click.argument('email')
def revoke_admin(email):
    user = _find(email)
    user.is_platform_admin = False
    db.session.commit()
    click.echo(f'{user.email} ya no es administrador de plataforma.')


@platform_cli.command('list-admins')
def list_admins():
    admins = User.query.filter_by(is_platform_admin=True).all()
    if not admins:
        click.echo('No hay administradores de plataforma.')
        return
    for user in admins:
        click.echo(f'  {user.email}  ({user.full_name})')


def register_cli(app):
    app.cli.add_command(platform_cli)
