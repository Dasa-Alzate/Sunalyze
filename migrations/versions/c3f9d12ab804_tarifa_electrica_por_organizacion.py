"""tarifa electrica por organizacion

Revision ID: c3f9d12ab804
Revises: b7e4a01c2f60
Create Date: 2026-09-27
"""
import sqlalchemy as sa
from alembic import op

revision = 'c3f9d12ab804'
down_revision = 'b7e4a01c2f60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'org_tariff_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=20), nullable=False, server_default=sa.text("'2.0TD'")),
        sa.Column('precio_punta', sa.Float(), nullable=False, server_default=sa.text('0.193')),
        sa.Column('precio_llano', sa.Float(), nullable=False, server_default=sa.text('0.135')),
        sa.Column('precio_valle', sa.Float(), nullable=False, server_default=sa.text('0.083')),
        sa.Column('precio_excedente', sa.Float(), nullable=False, server_default=sa.text('0.06')),
        sa.Column('precio_potencia_p1_dia', sa.Float(), nullable=False, server_default=sa.text('0.077')),
        sa.Column('precio_potencia_p2_dia', sa.Float(), nullable=False, server_default=sa.text('0.0077')),
        sa.Column('impuesto_electricidad', sa.Float(), nullable=False, server_default=sa.text('0.0511')),
        sa.Column('iva_pct', sa.Float(), nullable=False, server_default=sa.text('21.0')),
        sa.Column('alquiler_contador_mes', sa.Float(), nullable=False, server_default=sa.text('0.81')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', name='uq_org_tariff_org'),
    )
    with op.batch_alter_table('org_tariff_profiles', schema=None) as batch_op:
        batch_op.create_index('ix_org_tariff_profiles_org_id', ['org_id'])


def downgrade():
    with op.batch_alter_table('org_tariff_profiles', schema=None) as batch_op:
        batch_op.drop_index('ix_org_tariff_profiles_org_id')
    op.drop_table('org_tariff_profiles')
