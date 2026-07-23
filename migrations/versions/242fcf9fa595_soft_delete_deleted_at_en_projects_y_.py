from alembic import op
import sqlalchemy as sa

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
