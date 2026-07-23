from alembic import op
import sqlalchemy as sa

revision = 'f1a2b3c4d5e6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locale', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))
        batch_op.add_column(sa.Column('required_by', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('stage', sa.String(length=20), nullable=True))

    op.create_table(
        'org_branding_profiles',
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('logo_path', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=20), nullable=True),
        sa.Column('footer_text', sa.String(length=300), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'],
                                name=op.f('fk_org_branding_profiles_org_id_organizations')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_org_branding_profiles')),
        sa.UniqueConstraint('org_id', name='uq_org_branding_org'),
    )
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_org_branding_profiles_org_id'), ['org_id'],
                              unique=False)


def downgrade():
    with op.batch_alter_table('org_branding_profiles', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_org_branding_profiles_org_id'))
    op.drop_table('org_branding_profiles')

    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.drop_column('stage')
        batch_op.drop_column('required_by')
        batch_op.drop_column('currency')
        batch_op.drop_column('locale')
