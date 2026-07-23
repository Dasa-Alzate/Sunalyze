from alembic import op
import sqlalchemy as sa

revision = '67ad717ad9a4'
down_revision = '9a1c7e4b2f10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('financial_scenarios',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('assumptions', sa.Text(), nullable=True),
    sa.Column('results', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_financial_scenarios_created_by_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_financial_scenarios_org_id_organizations')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_financial_scenarios_project_id_projects')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_financial_scenarios'))
    )
    with op.batch_alter_table('financial_scenarios', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_financial_scenarios_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_financial_scenarios_project_id'), ['project_id'], unique=False)


def downgrade():
    with op.batch_alter_table('financial_scenarios', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_financial_scenarios_project_id'))
        batch_op.drop_index(batch_op.f('ix_financial_scenarios_org_id'))

    op.drop_table('financial_scenarios')
