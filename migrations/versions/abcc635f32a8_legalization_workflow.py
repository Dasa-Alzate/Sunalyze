"""legalization workflow

Revision ID: abcc635f32a8
Revises: 4ea694e9d6b2
Create Date: 2026-06-17 15:29:12.619757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abcc635f32a8'
down_revision = 'd808f3f9597f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('memoria_signatures',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('signed_by_user_id', sa.Integer(), nullable=False),
    sa.Column('pdf_sha256', sa.String(length=64), nullable=False),
    sa.Column('pdf_size_bytes', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('is_current', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_memoria_signatures_org_id_organizations')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_memoria_signatures_project_id_projects')),
    sa.ForeignKeyConstraint(['signed_by_user_id'], ['users.id'], name=op.f('fk_memoria_signatures_signed_by_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_memoria_signatures'))
    )
    with op.batch_alter_table('memoria_signatures', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_memoria_signatures_is_current'), ['is_current'], unique=False)
        batch_op.create_index(batch_op.f('ix_memoria_signatures_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_memoria_signatures_project_id'), ['project_id'], unique=False)

    op.create_table('project_events',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('from_estado', sa.String(length=20), nullable=True),
    sa.Column('to_estado', sa.String(length=20), nullable=False),
    sa.Column('note', sa.String(length=500), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_project_events_actor_user_id_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_project_events_org_id_organizations')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_project_events_project_id_projects')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_project_events'))
    )
    with op.batch_alter_table('project_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_project_events_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_project_events_project_id'), ['project_id'], unique=False)


def downgrade():
    with op.batch_alter_table('project_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_project_events_project_id'))
        batch_op.drop_index(batch_op.f('ix_project_events_org_id'))

    op.drop_table('project_events')
    with op.batch_alter_table('memoria_signatures', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_memoria_signatures_project_id'))
        batch_op.drop_index(batch_op.f('ix_memoria_signatures_org_id'))
        batch_op.drop_index(batch_op.f('ix_memoria_signatures_is_current'))

    op.drop_table('memoria_signatures')
