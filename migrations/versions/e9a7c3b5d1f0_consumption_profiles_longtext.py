"""Allow full-year consumption profiles in MySQL.

Revision ID: e9a7c3b5d1f0
Revises: c3f9d12ab804
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'e9a7c3b5d1f0'
down_revision = 'c3f9d12ab804'
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != 'mysql':
        return

    with op.batch_alter_table('consumption_profiles', schema=None) as batch_op:
        batch_op.alter_column(
            'source', existing_type=sa.Text(), type_=mysql.LONGTEXT(), nullable=True,
        )
        batch_op.alter_column(
            'fractions', existing_type=sa.Text(), type_=mysql.LONGTEXT(), nullable=True,
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'mysql':
        return

    oversized = bind.execute(sa.text(
        "SELECT COUNT(*) FROM consumption_profiles "
        "WHERE LENGTH(source) > 65535 OR LENGTH(fractions) > 65535"
    )).scalar_one()
    if oversized:
        raise RuntimeError(
            'Cannot downgrade consumption_profiles to TEXT: oversized profile data exists.'
        )

    with op.batch_alter_table('consumption_profiles', schema=None) as batch_op:
        batch_op.alter_column(
            'source', existing_type=mysql.LONGTEXT(), type_=sa.Text(), nullable=True,
        )
        batch_op.alter_column(
            'fractions', existing_type=mysql.LONGTEXT(), type_=sa.Text(), nullable=True,
        )