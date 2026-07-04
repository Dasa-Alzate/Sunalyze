# API map

Mapa autogenerado por `flask api-map`. Endpoints `/api`: 116.

No editar a mano: regenerar con `flask api-map`.

## admin

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/admin/flags` | `admin.list_flags` |  |
| POST | `/api/admin/flags` | `admin.upsert_flag` |  |
| DELETE | `/api/admin/flags/<key>/override` | `admin.clear_override` |  |
| POST | `/api/admin/flags/<key>/override` | `admin.set_override` |  |
| GET | `/api/admin/organizations` | `admin.list_orgs` |  |
| GET | `/api/admin/users` | `admin.list_users` |  |

## audit

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/audit` | `audit.list_audit` |  |

## auth

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| POST | `/api/auth/forgot-password` | `auth.forgot_password` |  |
| POST | `/api/auth/login` | `auth.login` |  |
| POST | `/api/auth/logout` | `auth.logout` |  |
| GET | `/api/auth/me` | `auth.me` |  |
| PATCH | `/api/auth/me` | `auth.update_me` |  |
| POST | `/api/auth/register` | `auth.register` |  |
| POST | `/api/auth/reset-password` | `auth.reset_password` |  |
| POST | `/api/auth/verify-email` | `auth.verify_email` |  |

## catalogs

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/catalogs` | `catalogs.list_catalogs` |  |
| POST | `/api/catalogs` | `catalogs.create_catalog` |  |
| DELETE | `/api/catalogs/<int:catalog_id>` | `catalogs.delete_catalog` |  |
| POST | `/api/catalogs/<int:catalog_id>/restore` | `catalogs.restore_catalog` |  |
| POST | `/api/catalogs/<int:catalog_id>/subscribe` | `catalogs.subscribe` |  |
| POST | `/api/catalogs/<int:catalog_id>/unsubscribe` | `catalogs.unsubscribe` |  |
| GET | `/api/marketplace` | `catalogs.marketplace` |  |

## circuit

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/circuit/<string:diagram_type>` | `circuit.get_diagram` |  |
| GET | `/api/circuit/templates` | `circuit.get_templates` |  |

## crud

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/<any(panels,inverters,batteries,wires):resource>` | `crud.list_equipment` |  |
| POST | `/api/<any(panels,inverters,batteries,wires):resource>` | `crud.create_equipment` |  |
| DELETE | `/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>` | `crud.delete_equipment` |  |
| GET | `/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>` | `crud.get_equipment` |  |
| PATCH | `/api/<any(panels,inverters,batteries,wires):resource>/<int:item_id>` | `crud.update_equipment` |  |
| POST | `/api/wires/calculate-section` | `crud.calculate_section` |  |
| GET | `/api/wires/search` | `crud.search_wires` |  |

## emails

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/emails` | `emails.list_emails` |  |
| GET | `/api/emails/<template_id>/preview` | `emails.preview_email` |  |
| POST | `/api/emails/<template_id>/send` | `emails.send_email` |  |

## finance

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| POST | `/api/projects/<int:project_id>/financial/compute` | `finance.compute_financial` |  |
| GET | `/api/projects/<int:project_id>/financial/scenarios` | `finance.list_scenarios` |  |
| POST | `/api/projects/<int:project_id>/financial/scenarios` | `finance.create_scenario` |  |
| DELETE | `/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>` | `finance.delete_scenario` |  |
| GET | `/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>` | `finance.get_scenario` |  |
| PATCH | `/api/projects/<int:project_id>/financial/scenarios/<int:scenario_id>` | `finance.update_scenario` |  |

## gdpr

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| DELETE | `/api/gdpr/account` | `gdpr.erase_account` |  |
| POST | `/api/gdpr/consent` | `gdpr.accept_privacy` |  |
| GET | `/api/gdpr/export` | `gdpr.export_data` |  |
| GET | `/api/gdpr/export.zip` | `gdpr.export_zip` |  |

## legalization

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/projects/<int:project_id>/legalization` | `legalization.get_legalization` |  |
| POST | `/api/projects/<int:project_id>/legalization/transition` | `legalization.transition` |  |
| POST | `/api/projects/<int:project_id>/memoria/sign` | `legalization.sign_memoria` |  |

## main

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| POST | `/api/diagrama-completo` | `main.diagrama_completo` |  |
| POST | `/api/panel-analysis` | `main.panel_analysis` |  |

## members

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| POST | `/api/invitations` | `members.create_invitation` |  |
| DELETE | `/api/invitations/<int:invitation_id>` | `members.revoke_invitation` |  |
| GET | `/api/invitations/<token>` | `members.get_invitation` |  |
| POST | `/api/invitations/<token>/accept` | `members.accept_invitation` |  |
| GET | `/api/members` | `members.list_team` |  |
| DELETE | `/api/members/<int:user_id>` | `members.remove_member` |  |
| PATCH | `/api/members/<int:user_id>` | `members.change_member_role` |  |

## modules

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/modules` | `modules.list_modules` |  |
| POST | `/api/modules/<key>/disable` | `modules.disable_module` |  |
| POST | `/api/modules/<key>/enable` | `modules.enable_module` |  |

## notifications

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/notifications` | `notifications.list_notifications` |  |
| POST | `/api/notifications/<int:notification_id>/read` | `notifications.mark_read` |  |
| POST | `/api/notifications/read-all` | `notifications.mark_all_read` |  |
| GET | `/api/notifications/unread-count` | `notifications.unread_count` |  |
| GET | `/api/pending-work` | `notifications.pending_work` |  |

## org

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/org/branding` | `org.get_branding` |  |
| PATCH | `/api/org/branding` | `org.update_branding` |  |

## posventa

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/installations` | `posventa.list_installations` |  |
| POST | `/api/installations` | `posventa.create_installation` |  |
| GET | `/api/installations/<int:installation_id>` | `posventa.get_installation` |  |
| PATCH | `/api/installations/<int:installation_id>` | `posventa.update_installation` |  |
| GET | `/api/installations/<int:installation_id>/incidents` | `posventa.list_incidents` |  |
| POST | `/api/installations/<int:installation_id>/incidents` | `posventa.create_incident` |  |
| DELETE | `/api/installations/<int:installation_id>/incidents/<int:incident_id>` | `posventa.delete_incident` |  |
| PATCH | `/api/installations/<int:installation_id>/incidents/<int:incident_id>` | `posventa.update_incident` |  |
| GET | `/api/installations/<int:installation_id>/maintenance` | `posventa.list_maintenance` |  |
| POST | `/api/installations/<int:installation_id>/maintenance` | `posventa.create_maintenance` |  |
| DELETE | `/api/installations/<int:installation_id>/maintenance/<int:visit_id>` | `posventa.delete_maintenance` |  |
| PATCH | `/api/installations/<int:installation_id>/maintenance/<int:visit_id>` | `posventa.update_maintenance` |  |
| GET | `/api/installations/<int:installation_id>/performance` | `posventa.get_performance` |  |
| GET | `/api/installations/<int:installation_id>/readings` | `posventa.list_readings` |  |
| POST | `/api/installations/<int:installation_id>/readings` | `posventa.create_reading` |  |
| DELETE | `/api/installations/<int:installation_id>/readings/<int:reading_id>` | `posventa.delete_reading` |  |
| PATCH | `/api/installations/<int:installation_id>/readings/<int:reading_id>` | `posventa.update_reading` |  |

## projects

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/projects` | `projects.list_projects` |  |
| POST | `/api/projects` | `projects.create_project` |  |
| DELETE | `/api/projects/<int:project_id>` | `projects.delete_project` |  |
| GET | `/api/projects/<int:project_id>` | `projects.get_project` |  |
| PATCH | `/api/projects/<int:project_id>` | `projects.update_project` |  |
| POST | `/api/projects/<int:project_id>/duplicate` | `projects.duplicate_project` |  |
| POST | `/api/projects/<int:project_id>/restore` | `projects.restore_project` |  |

## templates

| Método(s) | Ruta | Endpoint | Resumen |
| --- | --- | --- | --- |
| GET | `/api/documents/<int:doc_id>/download` | `templates.download_document` |  |
| GET | `/api/documents/jobs/<job_id>` | `templates.document_job_status` |  |
| GET | `/api/projects/<int:project_id>/documents` | `templates.list_project_documents` |  |
| GET | `/api/templates` | `templates.list_templates` |  |
| POST | `/api/templates` | `templates.create_template` |  |
| DELETE | `/api/templates/<int:template_id>` | `templates.delete_template` |  |
| GET | `/api/templates/<int:template_id>` | `templates.get_template` |  |
| PATCH | `/api/templates/<int:template_id>` | `templates.update_template` |  |
| PATCH | `/api/templates/<int:template_id>/content` | `templates.save_content` |  |
| POST | `/api/templates/<int:template_id>/generate` | `templates.generate_document` |  |
| POST | `/api/templates/<int:template_id>/install` | `templates.install_template` |  |
| POST | `/api/templates/<int:template_id>/preview` | `templates.preview_template` |  |
| POST | `/api/templates/<int:template_id>/publish` | `templates.publish_template` |  |
| GET | `/api/templates/bank` | `templates.list_bank` |  |
| GET | `/api/templates/categories` | `templates.list_categories` |  |
| POST | `/api/templates/categories` | `templates.create_category` |  |
| DELETE | `/api/templates/categories/<int:category_id>` | `templates.delete_category` |  |
| GET | `/api/templates/kinds` | `templates.list_kinds` |  |
| GET | `/api/templates/labels` | `templates.list_labels` |  |
| POST | `/api/templates/labels` | `templates.create_label` |  |
| GET | `/api/templates/library` | `templates.list_library` |  |
| DELETE | `/api/templates/library/<int:installation_id>` | `templates.uninstall_template` |  |
| POST | `/api/templates/library/<int:installation_id>/category` | `templates.categorize_installation` |  |
| POST | `/api/templates/library/<int:installation_id>/favorite` | `templates.favorite_installation` |  |
| POST | `/api/templates/library/<int:installation_id>/labels` | `templates.label_installation` |  |
| GET | `/api/templates/variables/<kind>` | `templates.list_variables` |  |
