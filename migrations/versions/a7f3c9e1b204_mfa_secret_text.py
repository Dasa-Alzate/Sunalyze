"""mfa_secret a Text para alojar el token Fernet cifrado

Revision ID: a7f3c9e1b204
Revises: 1d21aee9e755
Create Date: 2026-06-17 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a7f3c9e1b204'
down_revision = '1d21aee9e755'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('mfa_secret',
                              existing_type=sa.String(length=64),
                              type_=sa.Text(),
                              existing_nullable=True)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('mfa_secret',
                              existing_type=sa.Text(),
                              type_=sa.String(length=64),
                              existing_nullable=True)
