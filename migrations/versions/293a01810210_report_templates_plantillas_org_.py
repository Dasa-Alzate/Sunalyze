"""report templates: plantillas org + versiones + biblioteca

Revision ID: 293a01810210
Revises: c1052d9f2335
Create Date: 2026-06-22 12:59:36.802302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '293a01810210'
down_revision = 'c1052d9f2335'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('report_templates',
    sa.Column('org_id', sa.Integer(), nullable=True),
    sa.Column('scope', sa.String(length=10), nullable=False, server_default='org'),
    sa.Column('kind', sa.String(length=40), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('description', sa.String(length=500), nullable=True),
    sa.Column('country', sa.String(length=80), nullable=True),
    sa.Column('region', sa.String(length=120), nullable=True),
    sa.Column('thumbnail_path', sa.String(length=255), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
    sa.Column('is_official', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_report_templates_created_by_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_report_templates_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_report_templates'))
    )
    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_report_templates_kind'), ['kind'], unique=False)
        batch_op.create_index(batch_op.f('ix_report_templates_org_id'), ['org_id'], unique=False)

    op.create_table('template_categories',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_template_categories_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_categories')),
    sa.UniqueConstraint('org_id', 'name', name='uq_template_category_org_name')
    )
    with op.batch_alter_table('template_categories', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_template_categories_org_id'), ['org_id'], unique=False)

    op.create_table('template_labels',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_template_labels_org_id_organizations')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_labels')),
    sa.UniqueConstraint('org_id', 'name', name='uq_template_label_org_name')
    )
    with op.batch_alter_table('template_labels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_template_labels_org_id'), ['org_id'], unique=False)

    op.create_table('template_installations',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.Column('is_favorite', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    sa.Column('category_id', sa.Integer(), nullable=True),
    sa.Column('added_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['category_id'], ['template_categories.id'], name=op.f('fk_template_installations_category_id_template_categories')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_template_installations_org_id_organizations')),
    sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], name=op.f('fk_template_installations_template_id_report_templates')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_installations')),
    sa.UniqueConstraint('org_id', 'template_id', name='uq_installation_org_template')
    )
    with op.batch_alter_table('template_installations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_template_installations_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_template_installations_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_template_installations_template_id'), ['template_id'], unique=False)

    op.create_table('template_versions',
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
    sa.Column('content', sa.Text(), nullable=False, server_default='[]'),
    sa.Column('changelog', sa.String(length=500), nullable=True),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], name=op.f('fk_template_versions_template_id_report_templates')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_template_versions')),
    sa.UniqueConstraint('template_id', 'version', name='uq_template_version')
    )
    with op.batch_alter_table('template_versions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_template_versions_template_id'), ['template_id'], unique=False)

    op.create_table('installation_labels',
    sa.Column('installation_id', sa.Integer(), nullable=False),
    sa.Column('label_id', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['installation_id'], ['template_installations.id'], name=op.f('fk_installation_labels_installation_id_template_installations')),
    sa.ForeignKeyConstraint(['label_id'], ['template_labels.id'], name=op.f('fk_installation_labels_label_id_template_labels')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_installation_labels')),
    sa.UniqueConstraint('installation_id', 'label_id', name='uq_installation_label')
    )
    with op.batch_alter_table('installation_labels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_installation_labels_installation_id'), ['installation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_installation_labels_label_id'), ['label_id'], unique=False)


def downgrade():
    with op.batch_alter_table('installation_labels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_installation_labels_label_id'))
        batch_op.drop_index(batch_op.f('ix_installation_labels_installation_id'))

    op.drop_table('installation_labels')
    with op.batch_alter_table('template_versions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_template_versions_template_id'))

    op.drop_table('template_versions')
    with op.batch_alter_table('template_installations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_template_installations_template_id'))
        batch_op.drop_index(batch_op.f('ix_template_installations_org_id'))
        batch_op.drop_index(batch_op.f('ix_template_installations_category_id'))

    op.drop_table('template_installations')
    with op.batch_alter_table('template_labels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_template_labels_org_id'))

    op.drop_table('template_labels')
    with op.batch_alter_table('template_categories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_template_categories_org_id'))

    op.drop_table('template_categories')
    with op.batch_alter_table('report_templates', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_report_templates_org_id'))
        batch_op.drop_index(batch_op.f('ix_report_templates_kind'))

    op.drop_table('report_templates')
