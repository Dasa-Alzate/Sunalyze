from alembic import op
import sqlalchemy as sa

revision = 'c7f602e8e288'
down_revision = '13972b434fe3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('audit_events',
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('actor_email', sa.String(length=255), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('entity_type', sa.String(length=80), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('payload', sa.Text(), nullable=True),
    sa.Column('ip', sa.String(length=64), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_audit_events_actor_user_id_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_audit_events_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_events'))
    )
    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.create_index('ix_audit_events_org_created', ['org_id', 'created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_events_org_id'), ['org_id'], unique=False)

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('last_failed_login_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('lockout_until', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login_at')
        batch_op.drop_column('lockout_until')
        batch_op.drop_column('last_failed_login_at')
        batch_op.drop_column('failed_login_count')

    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audit_events_org_id'))
        batch_op.drop_index('ix_audit_events_org_created')

    op.drop_table('audit_events')
