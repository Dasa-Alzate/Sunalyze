
import sys
import unittest
from unittest import mock

from app import create_app
from app.extensions import limiter


def _make_app(overrides=None):
    config = {'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True,
              'WTF_CSRF_ENABLED': False}
    if overrides:
        config.update(overrides)
    return create_app(config)


class HealthEndpointTests(unittest.TestCase):

    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_health_ok_devuelve_200_y_shape(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'application/json')
        body = resp.get_json()
        self.assertEqual(set(body.keys()), {'status', 'db', 'cache'})
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['db'], 'ok')
        self.assertEqual(body['cache'], 'ok')

    def test_health_con_bd_caida_devuelve_503_degraded(self):
        with mock.patch('app.routes.health.db') as fake_db:
            fake_db.session.execute.side_effect = RuntimeError('db down')
            resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 503)
        body = resp.get_json()
        self.assertEqual(body['status'], 'degraded')
        self.assertEqual(body['db'], 'error')
        self.assertEqual(body['cache'], 'ok')

    def test_health_no_filtra_detalles_del_error(self):
        with mock.patch('app.routes.health.db') as fake_db:
            fake_db.session.execute.side_effect = RuntimeError('secreto-interno-123')
            resp = self.client.get('/health')
        self.assertNotIn(b'secreto-interno-123', resp.data)

    def test_fallo_de_cache_no_degrada_el_codigo_http(self):
        with mock.patch('app.routes.health.cache') as fake_cache:
            fake_cache.set.side_effect = RuntimeError('cache down')
            resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body['status'], 'ok')
        self.assertEqual(body['cache'], 'error')

    def test_health_no_lo_captura_el_catch_all_de_la_spa(self):
        self.assertEqual(
            self.app.view_functions[self.app.url_map.bind('localhost').match('/health')[0]].__module__,
            'app.routes.health',
        )
        resp = self.client.get('/health')
        self.assertEqual(resp.mimetype, 'application/json')
        spa = self.client.get('/ruta-inexistente-spa')
        self.assertEqual(spa.mimetype, 'text/html')

    def test_health_exento_del_rate_limit_default(self):
        app = _make_app({'RATELIMIT_DEFAULT': '2 per minute'})
        try:
            client = app.test_client()
            health_codes = [client.get('/health').status_code for _ in range(6)]
            self.assertEqual(health_codes, [200] * 6)
            spa_codes = [client.get('/ruta-limitada').status_code for _ in range(6)]
            self.assertIn(429, spa_codes)
        finally:
            limiter.limit_manager.set_default_limits([])


class SentryOptionalTests(unittest.TestCase):

    def test_sin_dsn_la_app_arranca_sin_importar_sentry(self):
        ya_importado = 'sentry_sdk' in sys.modules
        app = _make_app()
        self.assertIsNone(app.config['SENTRY_DSN'])
        if not ya_importado:
            self.assertNotIn('sentry_sdk', sys.modules)

    def test_defaults_de_config_sentry(self):
        app = _make_app()
        self.assertEqual(app.config['SENTRY_TRACES_SAMPLE_RATE'], 0.0)
        self.assertIn(app.config['SENTRY_ENVIRONMENT'], ('development', 'production'))


if __name__ == '__main__':
    unittest.main()
