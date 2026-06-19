"""Comandos de línea del portal de superadmin: bootstrap de acceso.

`flask superadmin grant <email>` da acceso (alta inicial del primer superadmin,
que no puede crearse desde la web). `revoke` y `list` complementan.
"""

import click
from flask.cli import AppGroup

from app.extensions import db
from app.models.user import User

superadmin_cli = AppGroup('superadmin', help='Gestión del portal de superadmin.')


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


def register_cli(app):
    app.cli.add_command(superadmin_cli)
