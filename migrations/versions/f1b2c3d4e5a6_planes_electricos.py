"""planes electricos de comercializadora

Revision ID: f1b2c3d4e5a6
Revises: e9a7c3b5d1f0
Create Date: 2026-10-06
"""
import sqlalchemy as sa
from alembic import op

revision = 'f1b2c3d4e5a6'
down_revision = 'e9a7c3b5d1f0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'electricity_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('comercializadora', sa.String(length=80), nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('peaje', sa.String(length=20), nullable=False, server_default=sa.text("'2.0TD'")),
        sa.Column('precio_punta', sa.Float(), nullable=False),
        sa.Column('precio_llano', sa.Float(), nullable=False),
        sa.Column('precio_valle', sa.Float(), nullable=False),
        sa.Column('precio_excedente', sa.Float(), nullable=False),
        sa.Column('precio_potencia_p1_dia', sa.Float(), nullable=False),
        sa.Column('precio_potencia_p2_dia', sa.Float(), nullable=False),
        sa.Column('impuesto_electricidad', sa.Float(), nullable=False),
        sa.Column('iva_pct', sa.Float(), nullable=False),
        sa.Column('alquiler_contador_mes', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('electricity_plans', schema=None) as batch_op:
        batch_op.create_index('ix_electricity_plans_org_id', ['org_id'])
        batch_op.create_index('ix_electricity_plans_deleted_at', ['deleted_at'])
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('electricity_plan_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_projects_electricity_plan_id', ['electricity_plan_id'])
        batch_op.create_foreign_key(
            'fk_projects_electricity_plan_id', 'electricity_plans',
            ['electricity_plan_id'], ['id'])


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_electricity_plan_id', type_='foreignkey')
        batch_op.drop_index('ix_projects_electricity_plan_id')
        batch_op.drop_column('electricity_plan_id')
    with op.batch_alter_table('electricity_plans', schema=None) as batch_op:
        batch_op.drop_index('ix_electricity_plans_deleted_at')
        batch_op.drop_index('ix_electricity_plans_org_id')
    op.drop_table('electricity_plans')
