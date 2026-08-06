from alembic import op
import sqlalchemy as sa

revision = 'a9b1c3d5e7f9'
down_revision = 'd5e7f9a1b3c5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('inverters', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mppt_v_min', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('mppt_v_max', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('mppt_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('isc_max_per_mppt', sa.Float(), nullable=True))
    with op.batch_alter_table('panels', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_series_fuse_a', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('panels', schema=None) as batch_op:
        batch_op.drop_column('max_series_fuse_a')
    with op.batch_alter_table('inverters', schema=None) as batch_op:
        batch_op.drop_column('isc_max_per_mppt')
        batch_op.drop_column('mppt_count')
        batch_op.drop_column('mppt_v_max')
        batch_op.drop_column('mppt_v_min')
