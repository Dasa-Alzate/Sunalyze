"""org branding project_prefix: prefijo del nº de serie de proyectos (configurable)

Anade `project_prefix` a `org_branding_profiles`. Nullable (no requiere server_default) y
batch-safe. La marca lo expone y valida (alfanumerico/guion, max 8, mayusculas); el uso real
en el serial de proyectos lo hara otra rama.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7f8a9b0c1d2'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_prefix', sa.String(length=8), nullable=True))


def downgrade():
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.drop_column('project_prefix')
