from alembic import op
import sqlalchemy as sa

revision = 'd4e6f8a0b2c4'
down_revision = 'b6c8d0e2f4a6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'org_budget_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('labor_fixed', sa.Float(), nullable=False, server_default='0'),
        sa.Column('labor_per_panel', sa.Float(), nullable=False, server_default='0'),
        sa.Column('equipment_inflation_pct', sa.Float(), nullable=False, server_default='0'),
        sa.Column('custom_lines', sa.Text(), nullable=True),
        sa.UniqueConstraint('org_id', name='uq_org_budget_org'),
    )
    op.create_index('ix_org_budget_profiles_org_id', 'org_budget_profiles', ['org_id'])

    for table in ('panels', 'inverters', 'batteries'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('precio_unitario', sa.Float(), nullable=True))
            batch_op.add_column(sa.Column('inflacion_pct', sa.Float(), nullable=True))

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('layout', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('layout')

    for table in ('batteries', 'inverters', 'panels'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('inflacion_pct')
            batch_op.drop_column('precio_unitario')

    op.drop_index('ix_org_budget_profiles_org_id', table_name='org_budget_profiles')
    op.drop_table('org_budget_profiles')
