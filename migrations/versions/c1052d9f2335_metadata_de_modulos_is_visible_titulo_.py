"""metadata de modulos (is_visible, titulo, imagenes, help_url, price)

Revision ID: c1052d9f2335
Revises: b64810c2d28c
Create Date: 2026-06-17 11:24:50.343322

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = 'c1052d9f2335'
down_revision = 'b64810c2d28c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('flags', sa.Column('titulo', sa.String(length=150), nullable=True))
    op.add_column('flags', sa.Column('is_visible', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('flags', sa.Column('image_path', sa.String(length=255), nullable=True))
    op.add_column('flags', sa.Column('thumbnail_path', sa.String(length=255), nullable=True))
    op.add_column('flags', sa.Column('help_url', sa.String(length=255), nullable=True))
    op.add_column('flags', sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True))
    with op.batch_alter_table('flags', schema=None) as batch_op:
        batch_op.alter_column('descripcion',
                   existing_type=mysql.VARCHAR(length=255),
                   type_=sa.String(length=500),
                   existing_nullable=True)


def downgrade():
    with op.batch_alter_table('flags', schema=None) as batch_op:
        batch_op.alter_column('descripcion',
                   existing_type=sa.String(length=500),
                   type_=mysql.VARCHAR(length=255),
                   existing_nullable=True)
    op.drop_column('flags', 'price')
    op.drop_column('flags', 'help_url')
    op.drop_column('flags', 'thumbnail_path')
    op.drop_column('flags', 'image_path')
    op.drop_column('flags', 'is_visible')
    op.drop_column('flags', 'titulo')
