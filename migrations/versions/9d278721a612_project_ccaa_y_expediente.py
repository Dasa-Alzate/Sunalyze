"""project ccaa y expediente

Revision ID: 9d278721a612
Revises: a1c0107ba5e5
Create Date: 2026-07-27

"""
from alembic import op
import sqlalchemy as sa

revision = '9d278721a612'
down_revision = 'a1c0107ba5e5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ccaa', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('expediente_numero', sa.String(length=60), nullable=True))
        batch_op.add_column(sa.Column('expediente_fecha', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('expediente_fecha')
        batch_op.drop_column('expediente_numero')
        batch_op.drop_column('ccaa')
