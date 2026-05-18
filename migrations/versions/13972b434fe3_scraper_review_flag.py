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
    """No-op tras la integración: needs_review/review_notes ya los crea la migración
    del portal de superadmin (c3357c982972). Se conserva el nodo de la cadena."""
    pass


def downgrade():
    pass
