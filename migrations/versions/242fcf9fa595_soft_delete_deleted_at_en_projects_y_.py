"""soft delete deleted_at en projects y catalogs

Revision ID: 242fcf9fa595
Revises: 827266176ee7
Create Date: 2026-06-22 15:30:22.436169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '242fcf9fa595'
down_revision = '827266176ee7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_catalogs_deleted_at'), ['deleted_at'], unique=False)

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_projects_deleted_at'), ['deleted_at'], unique=False)


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_projects_deleted_at'))
        batch_op.drop_column('deleted_at')

    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_catalogs_deleted_at'))
        batch_op.drop_column('deleted_at')
