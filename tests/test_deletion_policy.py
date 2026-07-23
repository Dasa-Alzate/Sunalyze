
import unittest

from sqlalchemy import event, text

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.memoria_signature import MemoriaSignature
from app.models.project_event import ProjectEvent
from app.models.financial_scenario import FinancialScenario
from app.models.installation import Installation, MaintenanceVisit
from app.models.audit_event import AuditEvent


class DeletionPolicyTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
        self.ctx = self.app.app_context()
        self.ctx.push()

        engine = db.engine

        @event.listens_for(engine, 'connect')
        def _enable_fk(dbapi_conn, _rec):
            cursor = dbapi_conn.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()

        self._fk_listener = _enable_fk
        db.create_all()
        db.session.execute(text('PRAGMA foreign_keys=ON'))

    def tearDown(self):
        event.remove(db.engine, 'connect', self._fk_listener)
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _user(self, email):
        u = User(email=email, first_name='T', last_name='User')
        u.set_password('secret123')
        db.session.add(u)
        db.session.flush()
        return u

    def _org(self, nombre='Org'):
        o = Organization(nombre=nombre)
        db.session.add(o)
        db.session.flush()
        return o

    def _project(self, org):
        p = Project(cliente='Cliente', org_id=org.id)
        db.session.add(p)
        db.session.flush()
        return p

    def test_fk_enforcement_is_active(self):
        with self.assertRaises(Exception):
            db.session.execute(
                text('INSERT INTO memberships (user_id, org_id, role) VALUES (99999, 88888, \'member\')')
            )
            db.session.commit()
        db.session.rollback()

    def test_hard_delete_project_cascades_children(self):
        org = self._org()
        user = self._user('owner@example.com')
        project = self._project(org)

        db.session.add_all([
            MemoriaSignature(org_id=org.id, project_id=project.id,
                             signed_by_user_id=user.id, pdf_sha256='a' * 64),
            ProjectEvent(org_id=org.id, project_id=project.id, to_estado='en_revision'),
            FinancialScenario(org_id=org.id, project_id=project.id, name='Contado'),
        ])
        installation = Installation(org_id=org.id, project_id=project.id)
        db.session.add(installation)
        db.session.flush()
        db.session.add(MaintenanceVisit(org_id=org.id, installation_id=installation.id))
        db.session.commit()

        pid, iid = project.id, installation.id
        db.session.execute(text('DELETE FROM projects WHERE id = :id'), {'id': pid})
        db.session.commit()

        self.assertEqual(MemoriaSignature.query.filter_by(project_id=pid).count(), 0)
        self.assertEqual(ProjectEvent.query.filter_by(project_id=pid).count(), 0)
        self.assertEqual(FinancialScenario.query.filter_by(project_id=pid).count(), 0)
        self.assertEqual(Installation.query.filter_by(id=iid).count(), 0)
        self.assertEqual(MaintenanceVisit.query.filter_by(installation_id=iid).count(), 0)

    def test_hard_delete_user_cascades_memberships(self):
        org = self._org()
        user = self._user('member@example.com')
        db.session.add(Membership(user_id=user.id, org_id=org.id, role='owner'))
        db.session.commit()

        uid = user.id
        db.session.execute(text('DELETE FROM users WHERE id = :id'), {'id': uid})
        db.session.commit()

        self.assertEqual(Membership.query.filter_by(user_id=uid).count(), 0)

    def test_hard_delete_actor_sets_null_and_keeps_record(self):
        org = self._org()
        user = self._user('actor@example.com')
        project = self._project(org)

        audit = AuditEvent(actor_user_id=user.id, actor_email=user.email,
                           org_id=org.id, action='project.updated')
        signature = MemoriaSignature(org_id=org.id, project_id=project.id,
                                     signed_by_user_id=user.id, pdf_sha256='b' * 64)
        db.session.add_all([audit, signature])
        db.session.commit()

        aid, sid, uid = audit.id, signature.id, user.id
        db.session.execute(text('DELETE FROM users WHERE id = :id'), {'id': uid})
        db.session.commit()

        surviving_audit = db.session.get(AuditEvent, aid)
        surviving_sig = db.session.get(MemoriaSignature, sid)
        self.assertIsNotNone(surviving_audit)
        self.assertIsNone(surviving_audit.actor_user_id)
        self.assertEqual(surviving_audit.actor_email, 'actor@example.com')
        self.assertIsNotNone(surviving_sig)
        self.assertIsNone(surviving_sig.signed_by_user_id)

    def test_soft_delete_still_works(self):
        user = self._user('soft@example.com')
        db.session.commit()

        self.assertFalse(user.is_deleted)
        user.soft_delete()
        db.session.commit()

        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)
        self.assertEqual(User.active().filter_by(id=user.id).count(), 0)
        self.assertEqual(User.with_deleted().filter_by(id=user.id).count(), 1)


if __name__ == '__main__':
    unittest.main()
