"""scraper review flag

Revision ID: 13972b434fe3
Revises: 02add458a3a3
Create Date: 2026-06-17 13:13:37.315474

"""
from alembic import op
import sqlalchemy as sa


revision = '13972b434fe3'
down_revision = '02add458a3a3'
branch_labels = None
depends_on = None


def upgrade():
    for table in ('inverters', 'panels'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('needs_review', sa.Boolean(),
                                          nullable=False, server_default=sa.text('0')))
            batch_op.add_column(sa.Column('review_notes', sa.String(length=500), nullable=True))


def downgrade():
    for table in ('panels', 'inverters'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('review_notes')
            batch_op.drop_column('needs_review')
