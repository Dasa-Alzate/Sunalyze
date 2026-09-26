"""perfiles de consumo

Revision ID: b7e4a01c2f60
Revises: cd95f044eadf
Create Date: 2026-09-26
"""
import sqlalchemy as sa
from alembic import op

revision = 'b7e4a01c2f60'
down_revision = 'cd95f044eadf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'consumption_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('origin', sa.String(length=10), nullable=False, server_default=sa.text("'ui'")),
        sa.Column('annual_kwh_hint', sa.Float(), nullable=True),
        sa.Column('cdm_version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('source', sa.Text(), nullable=True),
        sa.Column('fractions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('consumption_profiles', schema=None) as batch_op:
        batch_op.create_index('ix_consumption_profiles_org_id', ['org_id'])
        batch_op.create_index('ix_consumption_profiles_deleted_at', ['deleted_at'])
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('consumption_profile_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_projects_consumption_profile_id', ['consumption_profile_id'])
        batch_op.create_foreign_key(
            'fk_projects_consumption_profile_id', 'consumption_profiles',
            ['consumption_profile_id'], ['id'])


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_consumption_profile_id', type_='foreignkey')
        batch_op.drop_index('ix_projects_consumption_profile_id')
        batch_op.drop_column('consumption_profile_id')
    with op.batch_alter_table('consumption_profiles', schema=None) as batch_op:
        batch_op.drop_index('ix_consumption_profiles_deleted_at')
        batch_op.drop_index('ix_consumption_profiles_org_id')
    op.drop_table('consumption_profiles')
