from alembic import op
import sqlalchemy as sa

revision = 'c4d6e8f0a2b4'
down_revision = 'b3c5d7e9f1a2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('batteries', schema=None) as batch_op:
        batch_op.alter_column('voltage', existing_type=sa.Float(), nullable=True)


def downgrade():
    with op.batch_alter_table('batteries', schema=None) as batch_op:
        batch_op.alter_column('voltage', existing_type=sa.Float(), nullable=False)
