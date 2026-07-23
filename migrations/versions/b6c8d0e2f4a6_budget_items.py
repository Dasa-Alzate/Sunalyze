from alembic import op
import sqlalchemy as sa

revision = 'b6c8d0e2f4a6'
down_revision = 'a1c0107ba5e5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'budget_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capitulo', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('descripcion', sa.String(length=200), nullable=False),
        sa.Column('unidad', sa.String(length=10), nullable=False, server_default='ud'),
        sa.Column('cantidad', sa.Float(), nullable=False, server_default='1'),
        sa.Column('precio_unitario', sa.Float(), nullable=False, server_default='0'),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_budget_items_project_id', 'budget_items', ['project_id'])
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('budget_iva_pct', sa.Float(), nullable=False, server_default='21'))


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_column('budget_iva_pct')
    op.drop_index('ix_budget_items_project_id', table_name='budget_items')
    op.drop_table('budget_items')
