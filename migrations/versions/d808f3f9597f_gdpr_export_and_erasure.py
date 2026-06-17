"""gdpr export and erasure

Revision ID: d808f3f9597f
Revises: 4ea694e9d6b2
Create Date: 2026-06-17 15:29:31.503794

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd808f3f9597f'
down_revision = '4ea694e9d6b2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_organizations_deleted_at'), ['deleted_at'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('privacy_accepted_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deleted_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_deleted_at'), ['deleted_at'], unique=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_deleted_at'))
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('privacy_accepted_at')

    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_organizations_deleted_at'))
        batch_op.drop_column('deleted_at')
