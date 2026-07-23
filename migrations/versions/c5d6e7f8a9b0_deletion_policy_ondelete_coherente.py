from alembic import op
import sqlalchemy as sa

revision = 'c5d6e7f8a9b0'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

NAMING_CONVENTION = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
}

FK_CHANGES = {
    'memberships': [
        ('fk_memberships_user_id_users', 'users', ['user_id'], ['id'], 'CASCADE'),
        ('fk_memberships_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'org_branding_profiles': [
        ('fk_org_branding_profiles_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'catalogs': [
        ('fk_catalogs_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'catalog_subscriptions': [
        ('fk_catalog_subscriptions_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_catalog_subscriptions_catalog_id_catalogs', 'catalogs', ['catalog_id'], ['id'], 'CASCADE'),
    ],
    'projects': [
        ('fk_projects_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'installations': [
        ('fk_installations_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_installations_project_id_projects', 'projects', ['project_id'], ['id'], 'CASCADE'),
    ],
    'maintenance_visits': [
        ('fk_maintenance_visits_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_maintenance_visits_installation_id_installations', 'installations', ['installation_id'], ['id'], 'CASCADE'),
    ],
    'installation_incidents': [
        ('fk_installation_incidents_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_installation_incidents_installation_id_installations', 'installations', ['installation_id'], ['id'], 'CASCADE'),
    ],
    'production_readings': [
        ('fk_production_readings_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_production_readings_installation_id_installations', 'installations', ['installation_id'], ['id'], 'CASCADE'),
    ],
    'project_events': [
        ('fk_project_events_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_project_events_project_id_projects', 'projects', ['project_id'], ['id'], 'CASCADE'),
        ('fk_project_events_actor_user_id_users', 'users', ['actor_user_id'], ['id'], 'SET NULL'),
    ],
    'memoria_signatures': [
        ('fk_memoria_signatures_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_memoria_signatures_project_id_projects', 'projects', ['project_id'], ['id'], 'CASCADE'),
        ('fk_memoria_signatures_signed_by_user_id_users', 'users', ['signed_by_user_id'], ['id'], 'SET NULL'),
    ],
    'financial_scenarios': [
        ('fk_financial_scenarios_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_financial_scenarios_project_id_projects', 'projects', ['project_id'], ['id'], 'CASCADE'),
        ('fk_financial_scenarios_created_by_users', 'users', ['created_by'], ['id'], 'SET NULL'),
    ],
    'invitations': [
        ('fk_invitations_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_invitations_invited_by_user_id_users', 'users', ['invited_by_user_id'], ['id'], 'SET NULL'),
        ('fk_invitations_accepted_user_id_users', 'users', ['accepted_user_id'], ['id'], 'SET NULL'),
    ],
    'notifications': [
        ('fk_notifications_recipient_user_id_users', 'users', ['recipient_user_id'], ['id'], 'CASCADE'),
        ('fk_notifications_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_notifications_actor_user_id_users', 'users', ['actor_user_id'], ['id'], 'SET NULL'),
    ],
    'audit_events': [
        ('fk_audit_events_actor_user_id_users', 'users', ['actor_user_id'], ['id'], 'SET NULL'),
        ('fk_audit_events_org_id_organizations', 'organizations', ['org_id'], ['id'], 'SET NULL'),
    ],
    'support_tickets': [
        ('fk_support_tickets_requester_user_id_users', 'users', ['requester_user_id'], ['id'], 'SET NULL'),
        ('fk_support_tickets_org_id_organizations', 'organizations', ['org_id'], ['id'], 'SET NULL'),
    ],
    'support_ticket_messages': [
        ('fk_support_ticket_messages_ticket_id_support_tickets', 'support_tickets', ['ticket_id'], ['id'], 'CASCADE'),
    ],
    'superadmin_audit': [
        ('fk_superadmin_audit_actor_user_id_users', 'users', ['actor_user_id'], ['id'], 'SET NULL'),
    ],
    'flag_overrides': [
        ('fk_flag_overrides_flag_key_flags', 'flags', ['flag_key'], ['key'], 'CASCADE'),
        ('fk_flag_overrides_created_by_users', 'users', ['created_by'], ['id'], 'SET NULL'),
    ],
    'report_templates': [
        ('fk_report_templates_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_report_templates_created_by_users', 'users', ['created_by'], ['id'], 'SET NULL'),
    ],
    'template_versions': [
        ('fk_template_versions_template_id_report_templates', 'report_templates', ['template_id'], ['id'], 'CASCADE'),
    ],
    'template_categories': [
        ('fk_template_categories_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'template_labels': [
        ('fk_template_labels_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
    ],
    'template_installations': [
        ('fk_template_installations_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_template_installations_template_id_report_templates', 'report_templates', ['template_id'], ['id'], 'CASCADE'),
        ('fk_template_installations_category_id_template_categories', 'template_categories', ['category_id'], ['id'], 'SET NULL'),
    ],
    'installation_labels': [
        ('fk_installation_labels_installation_id_template_installations', 'template_installations', ['installation_id'], ['id'], 'CASCADE'),
        ('fk_installation_labels_label_id_template_labels', 'template_labels', ['label_id'], ['id'], 'CASCADE'),
    ],
    'generated_documents': [
        ('fk_generated_documents_org_id_organizations', 'organizations', ['org_id'], ['id'], 'CASCADE'),
        ('fk_generated_documents_project_id_projects', 'projects', ['project_id'], ['id'], 'CASCADE'),
        ('fk_generated_documents_template_id_report_templates', 'report_templates', ['template_id'], ['id'], 'CASCADE'),
        ('fk_generated_documents_template_version_id_template_versions', 'template_versions', ['template_version_id'], ['id'], 'CASCADE'),
        ('fk_generated_documents_generated_by_users', 'users', ['generated_by'], ['id'], 'SET NULL'),
    ],
}

NULLABLE_TO_TRUE = {
    'memoria_signatures': ['signed_by_user_id'],
    'invitations': ['invited_by_user_id'],
}


def _rebuild(table, ondelete_for):
    with op.batch_alter_table(table, schema=None, naming_convention=NAMING_CONVENTION) as batch_op:
        if table in NULLABLE_TO_TRUE:
            nullable = ondelete_for('SET NULL') is not None
            for column in NULLABLE_TO_TRUE[table]:
                batch_op.alter_column(column, existing_type=sa.Integer(), nullable=nullable)
        for name, referred, local_cols, remote_cols, ondelete in FK_CHANGES[table]:
            batch_op.drop_constraint(name, type_='foreignkey')
            batch_op.create_foreign_key(
                name, referred, local_cols, remote_cols,
                ondelete=ondelete_for(ondelete),
            )


def upgrade():
    for table in FK_CHANGES:
        _rebuild(table, ondelete_for=lambda ondelete: ondelete)


def downgrade():
    for table in reversed(list(FK_CHANGES)):
        _rebuild(table, ondelete_for=lambda ondelete: None)
