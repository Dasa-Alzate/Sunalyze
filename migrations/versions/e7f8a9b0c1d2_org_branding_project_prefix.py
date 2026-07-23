from alembic import op
import sqlalchemy as sa

revision = 'e7f8a9b0c1d2'
down_revision = 'd6e7f8a9b0c1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_prefix', sa.String(length=8), nullable=True))


def downgrade():
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.drop_column('project_prefix')
