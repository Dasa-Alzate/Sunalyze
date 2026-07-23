from alembic import op
import sqlalchemy as sa

revision = 'a1c0107ba5e5'
down_revision = 'e7a1c2d3b4f5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color', sa.String(length=9), nullable=True))


def downgrade():
    with op.batch_alter_table('catalogs', schema=None) as batch_op:
        batch_op.drop_column('color')
