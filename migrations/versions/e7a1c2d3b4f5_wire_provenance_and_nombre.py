"""provenance y nombre en wires (cables scrapeables)

Revision ID: e7a1c2d3b4f5
Revises: f2b7c1a9d4e0
Create Date: 2026-07-23 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'e7a1c2d3b4f5'
down_revision = 'f2b7c1a9d4e0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('wires', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nombre', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('source', sa.String(length=50), nullable=False, server_default='manual'))
        batch_op.add_column(sa.Column('source_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('external_id', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('scraped_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('needs_review', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('review_notes', sa.String(length=500), nullable=True))
        batch_op.create_index(batch_op.f('ix_wires_external_id'), ['external_id'], unique=False)


def downgrade():
    with op.batch_alter_table('wires', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wires_external_id'))
        batch_op.drop_column('review_notes')
        batch_op.drop_column('needs_review')
        batch_op.drop_column('is_locked')
        batch_op.drop_column('scraped_at')
        batch_op.drop_column('external_id')
        batch_op.drop_column('source_url')
        batch_op.drop_column('source')
        batch_op.drop_column('nombre')
