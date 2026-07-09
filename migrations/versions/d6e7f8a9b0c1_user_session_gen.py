"""user session_gen: revocacion de sesiones al cambiar contrasena (auditoria #2)

Anade `session_gen` a `users` con `server_default='0'` (batch-safe, seguro en tablas
con filas existentes). La cookie de sesion lleva este contador y `current_user()` exige
que coincida; `set_password` lo incrementa, invalidando todas las sesiones previas.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-07-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd6e7f8a9b0c1'
down_revision = 'c5d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('session_gen', sa.Integer(), nullable=False, server_default='0')
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('session_gen')
