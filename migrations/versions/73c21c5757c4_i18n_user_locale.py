from alembic import op
import sqlalchemy as sa

revision = '73c21c5757c4'
down_revision = '6f05e59255bc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale', sa.String(length=5), server_default='es', nullable=False))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('locale')
