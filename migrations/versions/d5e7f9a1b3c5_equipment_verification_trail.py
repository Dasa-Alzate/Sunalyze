from alembic import op
import sqlalchemy as sa

revision = 'd5e7f9a1b3c5'
down_revision = 'c4d6e8f0a2b4'
branch_labels = None
depends_on = None

_TABLES = ('panels', 'inverters', 'batteries', 'wires')


def upgrade():
    for table in _TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('verified_by', sa.String(length=255), nullable=True))
            batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))


def downgrade():
    for table in _TABLES:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.drop_column('verified_at')
            batch_op.drop_column('verified_by')
