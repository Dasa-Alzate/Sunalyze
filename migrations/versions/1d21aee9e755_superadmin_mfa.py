from alembic import op
import sqlalchemy as sa

revision = '1d21aee9e755'
down_revision = 'c3357c982972'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('mfa_secret', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('mfa_enabled', sa.Boolean(), nullable=False,
                                      server_default=sa.text('0')))
        batch_op.add_column(sa.Column('mfa_recovery_codes', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('mfa_recovery_codes')
        batch_op.drop_column('mfa_enabled')
        batch_op.drop_column('mfa_secret')
