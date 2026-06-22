"""batteries y relacion con proyecto

Revision ID: 9a1c7e4b2f10
Revises: 42edc2baf2b1
Create Date: 2026-06-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '9a1c7e4b2f10'
down_revision = '42edc2baf2b1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('batteries',
    sa.Column('catalog_id', sa.Integer(), nullable=True),
    sa.Column('nombre', sa.String(length=100), nullable=False),
    sa.Column('capacity_kwh', sa.Float(), nullable=False),
    sa.Column('power_kw', sa.Float(), nullable=False),
    sa.Column('voltage', sa.Float(), nullable=False),
    sa.Column('usable_kwh', sa.Float(), nullable=True),
    sa.Column('dod', sa.Float(), nullable=True),
    sa.Column('technology', sa.String(length=50), nullable=True),
    sa.Column('round_trip_efficiency', sa.Float(), nullable=True),
    sa.Column('max_cycles', sa.Integer(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('width', sa.Integer(), nullable=True),
    sa.Column('depth', sa.Integer(), nullable=True),
    sa.Column('datasheet', sa.String(length=200), nullable=True),
    sa.Column('source', sa.String(length=50), nullable=False, server_default='manual'),
    sa.Column('source_url', sa.String(length=500), nullable=True),
    sa.Column('external_id', sa.String(length=120), nullable=True),
    sa.Column('scraped_at', sa.DateTime(), nullable=True),
    sa.Column('is_locked', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('needs_review', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('review_notes', sa.String(length=500), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['catalog_id'], ['catalogs.id'], name=op.f('fk_batteries_catalog_id_catalogs')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_batteries')),
    sa.UniqueConstraint('nombre', name=op.f('uq_batteries_nombre'))
    )
    with op.batch_alter_table('batteries', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_batteries_catalog_id'), ['catalog_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_batteries_external_id'), ['external_id'], unique=False)

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('battery_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('battery_quantity', sa.Integer(), nullable=True, server_default='1'))
        batch_op.create_foreign_key(batch_op.f('fk_projects_battery_id_batteries'), 'batteries', ['battery_id'], ['id'])


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_projects_battery_id_batteries'), type_='foreignkey')
        batch_op.drop_column('battery_quantity')
        batch_op.drop_column('battery_id')

    with op.batch_alter_table('batteries', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_batteries_external_id'))
        batch_op.drop_index(batch_op.f('ix_batteries_catalog_id'))

    op.drop_table('batteries')
