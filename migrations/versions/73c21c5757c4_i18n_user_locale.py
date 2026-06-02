"""i18n: user.locale

Revision ID: 73c21c5757c4
Revises: 827266176ee7
Create Date: 2026-06-22 15:31:19.469305

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73c21c5757c4'
down_revision = '827266176ee7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale', sa.String(length=5), server_default='es', nullable=False))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('locale')
