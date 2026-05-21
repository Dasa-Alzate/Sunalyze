"""generated documents: pdf desde plantilla con version fijada

Revision ID: 42edc2baf2b1
Revises: 293a01810210
Create Date: 2026-06-22 13:19:18.688894

"""
from alembic import op
import sqlalchemy as sa


revision = '42edc2baf2b1'
down_revision = '293a01810210'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('generated_documents',
    sa.Column('org_id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.Column('template_version_id', sa.Integer(), nullable=False),
    sa.Column('kind', sa.String(length=40), nullable=False),
    sa.Column('pdf_path', sa.String(length=500), nullable=False),
    sa.Column('pdf_sha256', sa.String(length=64), nullable=False),
    sa.Column('pdf_size_bytes', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='generated'),
    sa.Column('generated_by', sa.Integer(), nullable=True),
    sa.Column('generated_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['generated_by'], ['users.id'], name=op.f('fk_generated_documents_generated_by_users')),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], name=op.f('fk_generated_documents_org_id_organizations')),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name=op.f('fk_generated_documents_project_id_projects')),
    sa.ForeignKeyConstraint(['template_id'], ['report_templates.id'], name=op.f('fk_generated_documents_template_id_report_templates')),
    sa.ForeignKeyConstraint(['template_version_id'], ['template_versions.id'], name=op.f('fk_generated_documents_template_version_id_template_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_generated_documents'))
    )
    with op.batch_alter_table('generated_documents', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_generated_documents_kind'), ['kind'], unique=False)
        batch_op.create_index(batch_op.f('ix_generated_documents_org_id'), ['org_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_generated_documents_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_generated_documents_template_id'), ['template_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_generated_documents_template_version_id'), ['template_version_id'], unique=False)


def downgrade():
    with op.batch_alter_table('generated_documents', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_generated_documents_template_version_id'))
        batch_op.drop_index(batch_op.f('ix_generated_documents_template_id'))
        batch_op.drop_index(batch_op.f('ix_generated_documents_project_id'))
        batch_op.drop_index(batch_op.f('ix_generated_documents_org_id'))
        batch_op.drop_index(batch_op.f('ix_generated_documents_kind'))

    op.drop_table('generated_documents')
