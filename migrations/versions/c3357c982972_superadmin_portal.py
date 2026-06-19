"""superadmin portal

Revision ID: c3357c982972
Revises: 4ea694e9d6b2
Create Date: 2026-06-17 13:32:57.345328

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3357c982972'
down_revision = '4ea694e9d6b2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('superadmin_audit',
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('actor_email', sa.String(length=255), nullable=True),
    sa.Column('ip', sa.String(length=64), nullable=True),
    sa.Column('action', sa.String(length=80), nullable=False),
    sa.Column('target', sa.String(length=200), nullable=True),
    sa.Column('detail', sa.Text(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], name=op.f('fk_superadmin_audit_actor_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_superadmin_audit'))
    )
    with op.batch_alter_table('superadmin_audit', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_superadmin_audit_action'), ['action'], unique=False)
        batch_op.create_index(batch_op.f('ix_superadmin_audit_actor_user_id'), ['actor_user_id'], unique=False)

    op.create_table('support_tickets',
    sa.Column('subject', sa.String(length=200), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('priority', sa.String(length=20), nullable=False),
    sa.Column('requester_email', sa.String(length=255), nullable=False),
    sa.Column('requester_user_id', sa.Integer(), nullable=True),
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_support_tickets_org_id_organizations')),
    sa.ForeignKeyConstraint(['requester_user_id'], ['users.id'], name=op.f('fk_support_tickets_requester_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_tickets'))
    )
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_tickets_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_requester_user_id'), ['requester_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_status'), ['status'], unique=False)

    op.create_table('support_ticket_messages',
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('author', sa.String(length=120), nullable=False),
    sa.Column('is_staff', sa.Boolean(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], name=op.f('fk_support_ticket_messages_ticket_id_support_tickets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_ticket_messages'))
    )
    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_ticket_messages_ticket_id'), ['ticket_id'], unique=False)

    for table in ('inverters', 'panels'):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.add_column(sa.Column('needs_review', sa.Boolean(),
                                          nullable=False, server_default=sa.text('0')))
            batch_op.add_column(sa.Column('review_notes', sa.String(length=500), nullable=True))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_superadmin', sa.Boolean(),
                                      nullable=False, server_default=sa.text('0')))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_superadmin')

    with op.batch_alter_table('panels', schema=None) as batch_op:
        batch_op.drop_column('review_notes')
        batch_op.drop_column('needs_review')

    with op.batch_alter_table('inverters', schema=None) as batch_op:
        batch_op.drop_column('review_notes')
        batch_op.drop_column('needs_review')

    with op.batch_alter_table('support_ticket_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_ticket_messages_ticket_id'))

    op.drop_table('support_ticket_messages')
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_tickets_status'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_requester_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_org_id'))

    op.drop_table('support_tickets')
    with op.batch_alter_table('superadmin_audit', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_superadmin_audit_actor_user_id'))
        batch_op.drop_index(batch_op.f('ix_superadmin_audit_action'))

    op.drop_table('superadmin_audit')
