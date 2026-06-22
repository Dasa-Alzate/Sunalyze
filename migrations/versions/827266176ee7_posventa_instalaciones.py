"""posventa instalaciones

Revision ID: 827266176ee7
Revises: 67ad717ad9a4
Create Date: 2026-06-22 15:05:56.958314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '827266176ee7'
down_revision = '67ad717ad9a4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('installations',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='operativa'),
    sa.Column('commissioned_at', sa.Date(), nullable=True),
    sa.Column('warranty_until', sa.Date(), nullable=True),
    sa.Column('expected_annual_kwh', sa.Float(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_installations_org_id_organizations')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_installations_project_id_projects')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_installations'))
    )
    with op.batch_alter_table('installations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_installations_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_installations_project_id'), ['project_id'], unique=True)

    op.create_table('installation_incidents',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('installation_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False, server_default=''),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=False, server_default='media'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='abierta'),
    sa.Column('opened_at', sa.Date(), nullable=True),
    sa.Column('resolved_at', sa.Date(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['installation_id'], ['installations.id'], name=op.f('fk_installation_incidents_installation_id_installations')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_installation_incidents_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_installation_incidents'))
    )
    with op.batch_alter_table('installation_incidents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_installation_incidents_installation_id'), ['installation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_installation_incidents_org_id'), ['org_id'], unique=False)

    op.create_table('maintenance_visits',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('installation_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False, server_default='preventivo'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='programada'),
    sa.Column('scheduled_at', sa.Date(), nullable=True),
    sa.Column('done_at', sa.Date(), nullable=True),
    sa.Column('technician', sa.String(length=150), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['installation_id'], ['installations.id'], name=op.f('fk_maintenance_visits_installation_id_installations')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_maintenance_visits_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_maintenance_visits'))
    )
    with op.batch_alter_table('maintenance_visits', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenance_visits_installation_id'), ['installation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_visits_org_id'), ['org_id'], unique=False)

    op.create_table('production_readings',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('installation_id', sa.Integer(), nullable=False),
    sa.Column('period', sa.String(length=20), nullable=False, server_default=''),
    sa.Column('actual_kwh', sa.Float(), nullable=False, server_default='0'),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['installation_id'], ['installations.id'], name=op.f('fk_production_readings_installation_id_installations')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_production_readings_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_production_readings'))
    )
    with op.batch_alter_table('production_readings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_production_readings_installation_id'), ['installation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_production_readings_org_id'), ['org_id'], unique=False)


def downgrade():
    with op.batch_alter_table('production_readings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_production_readings_org_id'))
        batch_op.drop_index(batch_op.f('ix_production_readings_installation_id'))

    op.drop_table('production_readings')
    with op.batch_alter_table('maintenance_visits', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenance_visits_org_id'))
        batch_op.drop_index(batch_op.f('ix_maintenance_visits_installation_id'))

    op.drop_table('maintenance_visits')
    with op.batch_alter_table('installation_incidents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_installation_incidents_org_id'))
        batch_op.drop_index(batch_op.f('ix_installation_incidents_installation_id'))

    op.drop_table('installation_incidents')
    with op.batch_alter_table('installations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_installations_project_id'))
        batch_op.drop_index(batch_op.f('ix_installations_org_id'))

    op.drop_table('installations')
