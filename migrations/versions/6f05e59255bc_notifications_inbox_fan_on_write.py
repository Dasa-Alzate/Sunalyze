from alembic import op
import sqlalchemy as sa

revision = '6f05e59255bc'
down_revision = '242fcf9fa595'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('notifications',
    sa.Column('recipient_user_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(length=80), nullable=False, server_default=''),
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('entity_type', sa.String(length=80), nullable=True),
    sa.Column('entity_id', sa.Integer(), nullable=True),
    sa.Column('payload', sa.Text(), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_notifications_actor_user_id_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_notifications_org_id_organizations')),
    sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], name=op.f('fk_notifications_recipient_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications'))
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notifications_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_notifications_read_at'), ['read_at'], unique=False)
        batch_op.create_index('ix_notifications_recipient_org', ['recipient_user_id', 'org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_notifications_recipient_user_id'), ['recipient_user_id'], unique=False)


def downgrade():
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notifications_recipient_user_id'))
        batch_op.drop_index('ix_notifications_recipient_org')
        batch_op.drop_index(batch_op.f('ix_notifications_read_at'))
        batch_op.drop_index(batch_op.f('ix_notifications_org_id'))

    op.drop_table('notifications')
