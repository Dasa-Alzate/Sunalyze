from alembic import op
import sqlalchemy as sa

revision = 'a7b9c1d3e5f7'
down_revision = 'd4e6f8a0b2c4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('wire_dc_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('wire_ac_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('wire_ground_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_projects_wire_dc', 'wires', ['wire_dc_id'], ['id'])
        batch_op.create_foreign_key('fk_projects_wire_ac', 'wires', ['wire_ac_id'], ['id'])
        batch_op.create_foreign_key('fk_projects_wire_ground', 'wires', ['wire_ground_id'], ['id'])


def downgrade():
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projects_wire_ground', type_='foreignkey')
        batch_op.drop_constraint('fk_projects_wire_ac', type_='foreignkey')
        batch_op.drop_constraint('fk_projects_wire_dc', type_='foreignkey')
        batch_op.drop_column('wire_ground_id')
        batch_op.drop_column('wire_ac_id')
        batch_op.drop_column('wire_dc_id')
