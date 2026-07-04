"""catalog scraper_name + is_active

Revision ID: a1b2c3d4e5f6
Revises: 73c21c5757c4
Create Date: 2026-06-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '73c21c5757c4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('catalogs', sa.Column('scraper_name', sa.String(length=100), nullable=True))
    op.add_column('catalogs', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index('ix_catalogs_scraper_name', 'catalogs', ['scraper_name'])
    catalogs = sa.table(
        'catalogs',
        sa.column('scraper_name', sa.String),
        sa.column('nombre', sa.String),
        sa.column('org_id', sa.Integer),
        sa.column('is_official', sa.Boolean),
    )
    op.execute(
        catalogs.update()
        .where(catalogs.c.org_id.is_(None))
        .where(catalogs.c.is_official == sa.true())
        .where(catalogs.c.scraper_name.is_(None))
        .values(scraper_name=sa.func.lower(catalogs.c.nombre))
    )


def downgrade():
    op.drop_index('ix_catalogs_scraper_name', table_name='catalogs')
    op.drop_column('catalogs', 'is_active')
    op.drop_column('catalogs', 'scraper_name')
