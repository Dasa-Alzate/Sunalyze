"""Tests de notificaciones (fan-on-write) y trabajo pendiente (derivado).

Verifica: fan-out al invitar/cambiar rol/expulsar/firmar memoria notifica a los
implicados pero NO al actor; unread-count correcto; read/read-all marcan; un
usuario no ve ni marca notificaciones de otro (IDOR -> 404); y que el trabajo
pendiente se deriva del estado vigente sin persistir filas (un proyecto en
borrador aparece y desaparece al cambiar de estado).
"""

import unittest

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership
from app.models.project import Project
from app.models.notification import Notification
from app.services.membership_service import MembershipService
from app.services.legalization_service import LegalizationService
from app.services.notification_service import NotificationService
from app.services.pending_work_service import PendingWorkService


def _make_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://',
                      WTF_CSRF_ENABLED=False)
    return app


class _Base(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self._seed()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed(self):
        self.org_a = Organization(nombre='Org A', type='BUSINESS', plan='pro', seats=10)
        self.org_b = Organization(nombre='Org B', type='BUSINESS', plan='pro', seats=10)
        db.session.add_all([self.org_a, self.org_b])
        db.session.flush()

        self.owner = User(email='owner@x.com', first_name='Owner', email_verified=True)
        self.owner.set_password('x')
        self.member = User(email='member@x.com', first_name='Member', email_verified=True)
        self.member.set_password('x')
        self.outsider = User(email='out@x.com', first_name='Out', email_verified=True)
        self.outsider.set_password('x')
        db.session.add_all([self.owner, self.member, self.outsider])
        db.session.flush()

        db.session.add_all([
            Membership(user_id=self.owner.id, org_id=self.org_a.id, role='owner'),
            Membership(user_id=self.member.id, org_id=self.org_a.id, role='member'),
            Membership(user_id=self.outsider.id, org_id=self.org_b.id, role='owner'),
        ])
        db.session.commit()

    def _login(self, user, org):
        client = self.app.test_client()
        with client.session_transaction() as sess:
            sess['user_id'] = user.id
            sess['org_id'] = org.id
        return client

    def _recipients(self, type=None):
        q = Notification.query
        if type:
            q = q.filter_by(type=type)
        return q.all()


class FanOutTest(_Base):
    def test_invite_notifies_existing_user_not_actor(self):
        MembershipService.invite(self.org_a.id, self.owner, self.outsider.email, 'member')
        notes = self._recipients('invitation.received')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].recipient_user_id, self.outsider.id)
        self.assertEqual(notes[0].actor_user_id, self.owner.id)
        self.assertNotEqual(notes[0].recipient_user_id, self.owner.id)

    def test_change_role_notifies_target_not_actor(self):
        MembershipService.change_role(self.org_a.id, self.owner, self.member.id, 'admin')
        notes = self._recipients('membership.role_changed')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].recipient_user_id, self.member.id)
        self.assertEqual(notes[0].to_dict()['payload']['to'], 'admin')

    def test_remove_notifies_expelled_not_actor(self):
        MembershipService.remove(self.org_a.id, self.owner, self.member.id)
        notes = self._recipients('membership.removed')
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].recipient_user_id, self.member.id)

    def test_sign_memoria_notifies_others_not_signer(self):
        project = Project(cliente='C', org_id=self.org_a.id, estado='borrador')
        db.session.add(project)
        db.session.commit()
        LegalizationService.sign_memoria(project, self.owner, 'a' * 64, 100)
        notes = self._recipients('memoria.signed')
        recipients = {n.recipient_user_id for n in notes}
        self.assertIn(self.member.id, recipients)
        self.assertNotIn(self.owner.id, recipients)
        self.assertEqual(len(notes), 1)

    def test_notify_excludes_actor_and_dedupes(self):
        created = NotificationService.notify(
            [self.owner.id, self.member.id, self.member.id], 'x.test',
            actor=self.owner, org_id=self.org_a.id,
        )
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].recipient_user_id, self.member.id)


class ReadStateTest(_Base):
    def test_unread_count_and_mark_read(self):
        NotificationService.notify([self.member.id], 'x.a', org_id=self.org_a.id)
        NotificationService.notify([self.member.id], 'x.b', org_id=self.org_a.id)
        db.session.commit()
        client = self._login(self.member, self.org_a)

        self.assertEqual(client.get('/api/notifications/unread-count').get_json()['unread_count'], 2)

        nid = client.get('/api/notifications').get_json()['items'][0]['id']
        client.post(f'/api/notifications/{nid}/read')
        self.assertEqual(client.get('/api/notifications/unread-count').get_json()['unread_count'], 1)

        client.post('/api/notifications/read-all')
        self.assertEqual(client.get('/api/notifications/unread-count').get_json()['unread_count'], 0)

    def test_list_scoped_to_active_org(self):
        NotificationService.notify([self.member.id], 'x.a', org_id=self.org_a.id)
        NotificationService.notify([self.member.id], 'x.b', org_id=self.org_b.id)
        db.session.commit()
        client = self._login(self.member, self.org_a)
        items = client.get('/api/notifications').get_json()['items']
        self.assertEqual(len(items), 1)


class IdorTest(_Base):
    def test_user_cannot_read_others_notification_404(self):
        created = NotificationService.notify([self.member.id], 'x.a', org_id=self.org_a.id)
        db.session.commit()
        nid = created[0].id
        client = self._login(self.owner, self.org_a)
        resp = client.post(f'/api/notifications/{nid}/read')
        self.assertEqual(resp.status_code, 404)

    def test_user_does_not_see_others_in_list(self):
        NotificationService.notify([self.member.id], 'x.a', org_id=self.org_a.id)
        db.session.commit()
        client = self._login(self.owner, self.org_a)
        self.assertEqual(client.get('/api/notifications').get_json()['total'], 0)


class PendingWorkTest(_Base):
    def test_draft_project_appears_and_disappears(self):
        project = Project(cliente='Borrador', org_id=self.org_a.id, estado='borrador')
        db.session.add(project)
        db.session.commit()

        derived = PendingWorkService.derive(self.owner, self.org_a.id)
        types = {i['type'] for i in derived['items']}
        self.assertIn('projects.draft', types)

        project.estado = 'aprobado'
        db.session.commit()
        derived2 = PendingWorkService.derive(self.owner, self.org_a.id)
        types2 = {i['type'] for i in derived2['items']}
        self.assertNotIn('projects.draft', types2)

    def test_pending_work_does_not_persist_rows(self):
        Project(cliente='B', org_id=self.org_a.id, estado='borrador')
        client = self._login(self.owner, self.org_a)
        before = Notification.query.count()
        client.get('/api/pending-work')
        client.get('/api/pending-work')
        self.assertEqual(Notification.query.count(), before)

    def test_endpoint_scoped_to_user_email_verification(self):
        self.member.email_verified = False
        db.session.commit()
        client = self._login(self.member, self.org_a)
        items = client.get('/api/pending-work').get_json()['items']
        types = {i['type'] for i in items}
        self.assertIn('account.email_unverified', types)


if __name__ == '__main__':
    unittest.main()
