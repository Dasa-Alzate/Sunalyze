from alembic import op
import sqlalchemy as sa

revision = 'b64810c2d28c'
down_revision = 'abcc635f32a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('flags',
    sa.Column('key', sa.String(length=80), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.String(length=255), nullable=True),
    sa.Column('default_enabled', sa.Boolean(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_flags'))
    )
    op.create_index(op.f('ix_flags_key'), 'flags', ['key'], unique=True)
    op.create_table('flag_overrides',
    sa.Column('flag_key', sa.String(length=80), nullable=False),
    sa.Column('scope', sa.String(length=10), nullable=False),
    sa.Column('scope_id', sa.Integer(), nullable=True),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_flag_overrides_created_by_users')),
    sa.ForeignKeyConstraint(['flag_key'], ['flags.key'], name=op.f('fk_flag_overrides_flag_key_flags')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_flag_overrides')),
    sa.UniqueConstraint('flag_key', 'scope', 'scope_id', name='uq_override_flag_scope')
    )
    op.create_index(op.f('ix_flag_overrides_flag_key'), 'flag_overrides', ['flag_key'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_flag_overrides_flag_key'), table_name='flag_overrides')
    op.drop_table('flag_overrides')
    op.drop_index(op.f('ix_flags_key'), table_name='flags')
    op.drop_table('flags')
