
import time
import unittest
from unittest import mock
from urllib.parse import urlparse, parse_qs

from app import create_app
from app.extensions import db, limiter
from app.gateways import tokens
from app.models.user import User, FAILED_LOGIN_THRESHOLD
from app.models.membership import Membership
from app.models.organization import Organization
from app.services.email_service import EmailService

VALID_PASSWORD = 'CorrectHorse7Battery!'
NEW_PASSWORD = 'Staple9Lantern#Verde'
CSRF_ERROR_MESSAGE = 'Token CSRF inválido o ausente. Recarga la página.'


def _make_app(csrf_enabled=False):
    return create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'TESTING': True,
        'WTF_CSRF_ENABLED': csrf_enabled,
        'RATELIMIT_ENABLED': False,
    })


def _token_from_url(url):
    return parse_qs(urlparse(url).query)['token'][0]


class AuthFlowTestBase(unittest.TestCase):
    csrf_enabled = False

    def setUp(self):
        previous_limiter_state = limiter.enabled
        self.app = _make_app(csrf_enabled=self.csrf_enabled)
        self.addCleanup(setattr, limiter, 'enabled', previous_limiter_state)
        with self.app.app_context():
            db.create_all()
        self.sent_emails = []
        patcher = mock.patch.object(EmailService, 'send', side_effect=self._capture_email)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _capture_email(self, template_id, to, context=None, locale=None):
        self.sent_emails.append({'template': template_id, 'to': to, 'context': context or {}})
        return {'to': to, 'sent': False, 'reason': 'captured'}

    def _register(self, client, email, password=VALID_PASSWORD, company='', first_name='Ana'):
        return client.post('/api/auth/register', json={
            'email': email, 'password': password,
            'first_name': first_name, 'company': company,
        })

    def _login(self, client, email, password, remember=False):
        return client.post('/api/auth/login', json={
            'email': email, 'password': password, 'remember': remember,
        })

    def _fresh_user(self, email, password=VALID_PASSWORD, company=''):
        resp = self._register(self.app.test_client(), email, password, company)
        assert resp.status_code == 201, resp.get_json()
        self.sent_emails.clear()
        return resp.get_json()['user']['id']

    def _issue_token(self, purpose, uid, age_seconds=0):
        with self.app.app_context():
            if age_seconds:
                with mock.patch('time.time', return_value=time.time() - age_seconds):
                    return tokens.issue(purpose, {'uid': uid})
            return tokens.issue(purpose, {'uid': uid})


class RegistrationFlowTest(AuthFlowTestBase):

    def test_register_creates_user_org_and_owner_membership(self):
        cases = [
            ('personal@example.com', '', 'PERSONAL', 'Mi espacio', 1),
            ('empresa@example.com', 'Acme Solar', 'BUSINESS', 'Acme Solar', 5),
        ]
        for email, company, org_type, org_name, seats in cases:
            with self.subTest(org_type=org_type):
                resp = self._register(self.app.test_client(), email, company=company)
                self.assertEqual(resp.status_code, 201)
                body = resp.get_json()
                self.assertEqual(body['user']['email'], email)
                self.assertEqual(body['role'], 'owner')
                with self.app.app_context():
                    user = User.query.filter_by(email=email).one()
                    membership = Membership.query.filter_by(user_id=user.id).one()
                    self.assertEqual(membership.role, 'owner')
                    org = db.session.get(Organization, membership.org_id)
                    self.assertEqual(
                        (org.type, org.nombre, org.seats), (org_type, org_name, seats),
                    )

    def test_register_sends_verification_email_with_working_token(self):
        resp = self._register(self.app.test_client(), 'nueva@example.com')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(len(self.sent_emails), 1)
        email = self.sent_emails[0]
        self.assertEqual((email['template'], email['to']), ('welcome', 'nueva@example.com'))
        self.assertIn('/verificar?token=', email['context']['cta_url'])
        token = _token_from_url(email['context']['cta_url'])
        verify = self.app.test_client().post('/api/auth/verify-email', json={'token': token})
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.get_json()['user']['email_verified'])
        with self.app.app_context():
            self.assertTrue(User.query.filter_by(email='nueva@example.com').one().email_verified)

    def test_register_logs_user_in_before_verification(self):
        client = self.app.test_client()
        self._register(client, 'directa@example.com')
        me = client.get('/api/auth/me').get_json()
        self.assertEqual(me['user']['email'], 'directa@example.com')
        self.assertFalse(me['user']['email_verified'])

    def test_register_rejects_weak_passwords(self):
        weak = [
            ('demasiado corta', 'corta123'),
            ('demasiado larga', 'Aa1!' * 33),
            ('filtrada comun', 'password123'),
            ('filtrada comun mayusculas', 'PASSWORD123'),
            ('baja diversidad', 'abababababab'),
        ]
        for name, password in weak:
            with self.subTest(caso=name):
                resp = self._register(self.app.test_client(), 'debil@example.com', password=password)
                body = resp.get_json()
                self.assertEqual(resp.status_code, 422)
                self.assertEqual(body['code'], 'error.validation')
                self.assertTrue(any(d['field'] == 'password' for d in body['details']))
        with self.app.app_context():
            self.assertIsNone(User.query.filter_by(email='debil@example.com').first())

    def test_register_duplicate_email_conflict_case_insensitive(self):
        self._fresh_user('dupe@example.com')
        for attempt in ('dupe@example.com', 'DUPE@example.com'):
            with self.subTest(email=attempt):
                resp = self._register(self.app.test_client(), attempt)
                self.assertEqual(resp.status_code, 409)
                self.assertEqual(resp.get_json()['code'], 'auth.email_taken')
        with self.app.app_context():
            self.assertEqual(User.query.filter(User.email.ilike('dupe@example.com')).count(), 1)


class EmailVerificationTest(AuthFlowTestBase):

    def test_invalid_tokens_fail_cleanly(self):
        uid = self._fresh_user('averificar@example.com')
        good = self._issue_token(tokens.VERIFY_EMAIL, uid)
        cases = [
            ('token corto', '1234567', 'error.validation'),
            ('token basura', 'x' * 40, 'token.invalid'),
            ('token manipulado', good + 'x', 'token.invalid'),
            ('proposito equivocado', self._issue_token(tokens.RESET_PASSWORD, uid), 'token.invalid'),
        ]
        for name, token, code in cases:
            with self.subTest(caso=name):
                resp = self.app.test_client().post('/api/auth/verify-email', json={'token': token})
                self.assertEqual(resp.status_code, 422)
                self.assertEqual(resp.get_json()['code'], code)
        with self.app.app_context():
            self.assertFalse(db.session.get(User, uid).email_verified)

    def test_expired_token_fails_with_expired_code(self):
        uid = self._fresh_user('caducada@example.com')
        stale = self._issue_token(tokens.VERIFY_EMAIL, uid, age_seconds=8 * 86400)
        resp = self.app.test_client().post('/api/auth/verify-email', json={'token': stale})
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['code'], 'token.expired')

    def test_unverified_account_can_log_in(self):
        self._fresh_user('sinverificar@example.com')
        client = self.app.test_client()
        resp = self._login(client, 'sinverificar@example.com', VALID_PASSWORD)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.get_json()['user']['email_verified'])
        self.assertEqual(client.get('/api/members').status_code, 200)


class LoginLogoutTest(AuthFlowTestBase):

    def test_login_grants_working_session(self):
        self._fresh_user('activa@example.com')
        client = self.app.test_client()
        resp = self._login(client, 'activa@example.com', VALID_PASSWORD)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['role'], 'owner')
        self.assertEqual(client.get('/api/auth/me').get_json()['user']['email'], 'activa@example.com')
        self.assertEqual(client.get('/api/members').status_code, 200)

    def test_bad_credentials_do_not_leak_which_field_failed(self):
        self._fresh_user('victima@example.com')
        wrong_password = self._login(self.app.test_client(), 'victima@example.com', 'MalaPassword123!')
        unknown_email = self._login(self.app.test_client(), 'nadie@example.com', VALID_PASSWORD)
        for name, resp in (('password mala', wrong_password), ('email inexistente', unknown_email)):
            with self.subTest(caso=name):
                self.assertEqual(resp.status_code, 401)
                self.assertEqual(resp.get_json()['code'], 'auth.invalid_credentials')
        self.assertEqual(wrong_password.get_json(), unknown_email.get_json())

    def test_remember_controls_session_cookie_persistence(self):
        self._fresh_user('cookies@example.com')
        for remember, persistent in ((True, True), (False, False)):
            with self.subTest(remember=remember):
                client = self.app.test_client()
                resp = self._login(client, 'cookies@example.com', VALID_PASSWORD, remember=remember)
                session_cookies = [
                    h for h in resp.headers.getlist('Set-Cookie') if h.startswith('session=')
                ]
                self.assertEqual(len(session_cookies), 1)
                self.assertEqual('Expires=' in session_cookies[0], persistent)

    def test_logout_invalidates_session(self):
        self._fresh_user('saliente@example.com')
        client = self.app.test_client()
        self._login(client, 'saliente@example.com', VALID_PASSWORD)
        self.assertEqual(client.post('/api/auth/logout').status_code, 200)
        self.assertIsNone(client.get('/api/auth/me').get_json()['user'])
        self.assertEqual(client.get('/api/members').status_code, 401)

    def test_logout_without_session_is_idempotent(self):
        self.assertEqual(self.app.test_client().post('/api/auth/logout').status_code, 200)

    def test_lockout_after_failed_attempts_blocks_even_correct_password(self):
        self._fresh_user('bloqueada@example.com')
        client = self.app.test_client()
        for attempt in range(FAILED_LOGIN_THRESHOLD):
            with self.subTest(intento=attempt + 1):
                resp = self._login(client, 'bloqueada@example.com', 'MalaPassword123!')
                self.assertEqual(resp.status_code, 401)
        locked = self._login(client, 'bloqueada@example.com', VALID_PASSWORD)
        self.assertEqual(locked.status_code, 403)
        self.assertEqual(locked.get_json()['code'], 'auth.account_locked')

    def test_successful_login_resets_failure_counter(self):
        uid = self._fresh_user('resiliente@example.com')
        client = self.app.test_client()
        for _ in range(FAILED_LOGIN_THRESHOLD - 1):
            self._login(client, 'resiliente@example.com', 'MalaPassword123!')
        ok = self._login(client, 'resiliente@example.com', VALID_PASSWORD)
        self.assertEqual(ok.status_code, 200)
        with self.app.app_context():
            user = db.session.get(User, uid)
            self.assertEqual(user.failed_login_count, 0)
            self.assertIsNone(user.lockout_until)


class PasswordResetTest(AuthFlowTestBase):

    def _request_reset(self, email):
        resp = self.app.test_client().post('/api/auth/forgot-password', json={'email': email})
        self.assertEqual(resp.status_code, 200)
        return resp

    def _reset_token_for(self, email):
        self._request_reset(email)
        return _token_from_url(self.sent_emails[-1]['context']['reset_url'])

    def test_forgot_sends_email_with_token_only_for_known_accounts(self):
        self._fresh_user('olvidadiza@example.com')
        known = self._request_reset('olvidadiza@example.com')
        self.assertEqual(len(self.sent_emails), 1)
        email = self.sent_emails[0]
        self.assertEqual((email['template'], email['to']), ('reset-password', 'olvidadiza@example.com'))
        self.assertIn('/reset-password?token=', email['context']['reset_url'])
        unknown = self._request_reset('fantasma@example.com')
        self.assertEqual(len(self.sent_emails), 1)
        self.assertEqual(known.get_json()['message'], unknown.get_json()['message'])
        self.assertIsNone(unknown.get_json()['reset_link'])

    def test_reset_with_valid_token_rotates_the_effective_password(self):
        self._fresh_user('renovada@example.com')
        token = self._reset_token_for('renovada@example.com')
        resp = self.app.test_client().post('/api/auth/reset-password',
                                           json={'token': token, 'password': NEW_PASSWORD})
        self.assertEqual(resp.status_code, 200)
        old = self._login(self.app.test_client(), 'renovada@example.com', VALID_PASSWORD)
        self.assertEqual(old.status_code, 401)
        new = self._login(self.app.test_client(), 'renovada@example.com', NEW_PASSWORD)
        self.assertEqual(new.status_code, 200)

    def test_reset_enforces_password_policy(self):
        self._fresh_user('estricta@example.com')
        token = self._reset_token_for('estricta@example.com')
        resp = self.app.test_client().post('/api/auth/reset-password',
                                           json={'token': token, 'password': 'corta123'})
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.get_json()['code'], 'error.validation')
        still = self._login(self.app.test_client(), 'estricta@example.com', VALID_PASSWORD)
        self.assertEqual(still.status_code, 200)

    def test_invalid_and_expired_reset_tokens_fail(self):
        uid = self._fresh_user('segura@example.com')
        cases = [
            ('token basura', 'y' * 40, 'token.invalid'),
            ('token de verify', self._issue_token(tokens.VERIFY_EMAIL, uid), 'token.invalid'),
            ('token caducado', self._issue_token(tokens.RESET_PASSWORD, uid, age_seconds=2 * 3600),
             'token.expired'),
        ]
        for name, token, code in cases:
            with self.subTest(caso=name):
                resp = self.app.test_client().post('/api/auth/reset-password',
                                                   json={'token': token, 'password': NEW_PASSWORD})
                self.assertEqual(resp.status_code, 422)
                self.assertEqual(resp.get_json()['code'], code)
        self.assertEqual(self._login(self.app.test_client(), 'segura@example.com',
                                     VALID_PASSWORD).status_code, 200)

    def test_reset_token_is_single_use(self):
        self._fresh_user('reusada@example.com')
        token = self._reset_token_for('reusada@example.com')
        first = self.app.test_client().post('/api/auth/reset-password',
                                            json={'token': token, 'password': NEW_PASSWORD})
        self.assertEqual(first.status_code, 200)
        second = self.app.test_client().post('/api/auth/reset-password',
                                             json={'token': token, 'password': 'Otra9Clave#Distinta'})
        self.assertEqual(second.status_code, 422)
        self.assertEqual(second.get_json()['code'], 'token.invalid')
        relogin = self._login(self.app.test_client(), 'reusada@example.com', NEW_PASSWORD)
        self.assertEqual(relogin.status_code, 200)
        rejected = self._login(self.app.test_client(), 'reusada@example.com', 'Otra9Clave#Distinta')
        self.assertEqual(rejected.status_code, 401)


class CsrfContractTest(AuthFlowTestBase):

    csrf_enabled = True

    def _csrf_ready_client(self):
        client = self.app.test_client()
        client.get('/api/auth/me')
        return client, client.get_cookie('csrf_token').value

    def test_mutation_without_csrf_token_is_rejected(self):
        client, _ = self._csrf_ready_client()
        resp = self._login(client, 'alguien@example.com', VALID_PASSWORD)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()['error'], CSRF_ERROR_MESSAGE)

    def test_mutation_with_forged_csrf_token_is_rejected(self):
        client, _ = self._csrf_ready_client()
        resp = client.post('/api/auth/login',
                           json={'email': 'alguien@example.com', 'password': VALID_PASSWORD},
                           headers={'X-CSRFToken': 'forjado.no-valido'})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()['error'], CSRF_ERROR_MESSAGE)

    def test_spa_token_mechanism_allows_the_full_auth_cycle(self):
        client, token = self._csrf_ready_client()
        register = client.post('/api/auth/register',
                               json={'email': 'spa@example.com', 'password': VALID_PASSWORD,
                                     'first_name': 'Ana'},
                               headers={'X-CSRFToken': token})
        self.assertEqual(register.status_code, 201)
        logout = client.post('/api/auth/logout',
                             headers={'X-CSRFToken': client.get_cookie('csrf_token').value})
        self.assertEqual(logout.status_code, 200)
        self.assertIsNone(client.get('/api/auth/me').get_json()['user'])
        login = client.post('/api/auth/login',
                            json={'email': 'spa@example.com', 'password': VALID_PASSWORD},
                            headers={'X-CSRFToken': client.get_cookie('csrf_token').value})
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.get_json()['user']['email'], 'spa@example.com')


class InvitationAuthTest(AuthFlowTestBase):

    def _owner_with_team_org(self):
        client = self.app.test_client()
        resp = self._register(client, 'owner@acme.com', company='Acme Solar')
        self.assertEqual(resp.status_code, 201)
        self.sent_emails.clear()
        return client

    def test_invitation_happy_path_creates_membership_with_invited_role(self):
        owner = self._owner_with_team_org()
        invite = owner.post('/api/invitations', json={'email': 'invitada@acme.com', 'role': 'member'})
        self.assertEqual(invite.status_code, 201)
        email = self.sent_emails[-1]
        self.assertEqual((email['template'], email['to']), ('invitation', 'invitada@acme.com'))
        token = _token_from_url(email['context']['accept_url'])
        invitee = self.app.test_client()
        self._register(invitee, 'invitada@acme.com')
        accept = invitee.post(f'/api/invitations/{token}/accept')
        self.assertEqual(accept.status_code, 201)
        body = accept.get_json()
        self.assertEqual(body['role'], 'member')
        with self.app.app_context():
            member = User.query.filter_by(email='invitada@acme.com').one()
            membership = Membership.query.filter_by(user_id=member.id, org_id=body['org_id']).one()
            self.assertEqual(membership.role, 'member')
        self.assertEqual(invitee.get('/api/auth/me').get_json()['role'], 'member')

    def test_invitation_accept_error_contract(self):
        owner = self._owner_with_team_org()
        owner.post('/api/invitations', json={'email': 'pendiente@acme.com', 'role': 'member'})
        token = _token_from_url(self.sent_emails[-1]['context']['accept_url'])
        anonymous = self.app.test_client()
        stranger = self.app.test_client()
        self._register(stranger, 'externa@example.com')
        cases = [
            ('sin sesion', anonymous, token, 401, None),
            ('token inexistente', stranger, 'no-existe-token', 404, 'invitation.not_found'),
        ]
        for name, client, tok, status, code in cases:
            with self.subTest(caso=name):
                resp = client.post(f'/api/invitations/{tok}/accept')
                self.assertEqual(resp.status_code, status)
                if code:
                    self.assertEqual(resp.get_json()['code'], code)

    def test_accepted_invitation_cannot_be_replayed(self):
        owner = self._owner_with_team_org()
        owner.post('/api/invitations', json={'email': 'unica@acme.com', 'role': 'admin'})
        token = _token_from_url(self.sent_emails[-1]['context']['accept_url'])
        invitee = self.app.test_client()
        self._register(invitee, 'unica@acme.com')
        self.assertEqual(invitee.post(f'/api/invitations/{token}/accept').status_code, 201)
        replay = invitee.post(f'/api/invitations/{token}/accept')
        self.assertEqual(replay.status_code, 409)


if __name__ == '__main__':
    unittest.main()
