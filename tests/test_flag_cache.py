"""Tests de la cache de resolución de feature flags.

Fija dos invariantes: (1) la segunda resolución idéntica se sirve de cache sin
tocar la BD; (2) cualquier escritura (upsert, override, clear) invalida la
cache y el cambio es visible inmediatamente, sin esperar al TTL.
"""

import unittest

from sqlalchemy import event

from app import create_app
from app.extensions import db
from app.services.flag_service import FlagService


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class _QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0

    def __enter__(self):
        event.listen(self.engine, 'before_cursor_execute', self._record)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, 'before_cursor_execute', self._record)

    def _record(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1


class FlagCacheTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        FlagService.upsert_flag('demo_feature', nombre='Demo', default_enabled=False)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_second_resolution_hits_cache_without_queries(self):
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1, user_id=2))
        with _QueryCounter(db.engine) as counter:
            self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1, user_id=2))
        self.assertEqual(counter.count, 0)

    def test_toggle_via_override_is_visible_immediately(self):
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1))
        FlagService.set_override('demo_feature', 'global', None, True)
        self.assertTrue(FlagService.is_enabled('demo_feature', org_id=1))
        FlagService.set_override('demo_feature', 'global', None, False)
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1))

    def test_clear_override_is_visible_immediately(self):
        FlagService.set_override('demo_feature', 'org', 7, True)
        self.assertTrue(FlagService.is_enabled('demo_feature', org_id=7))
        FlagService.clear_override('demo_feature', 'org', 7)
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=7))

    def test_upsert_default_change_is_visible_immediately(self):
        self.assertFalse(FlagService.is_enabled('demo_feature'))
        FlagService.upsert_flag('demo_feature', default_enabled=True)
        self.assertTrue(FlagService.is_enabled('demo_feature'))

    def test_cache_key_granularity_per_scope(self):
        FlagService.set_override('demo_feature', 'user', 42, True)
        self.assertTrue(FlagService.is_enabled('demo_feature', org_id=1, user_id=42))
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1, user_id=43))
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=1))

    def test_org_override_beats_global_and_user_beats_org(self):
        FlagService.set_override('demo_feature', 'global', None, False)
        FlagService.set_override('demo_feature', 'org', 5, True)
        self.assertTrue(FlagService.is_enabled('demo_feature', org_id=5))
        FlagService.set_override('demo_feature', 'user', 9, False)
        self.assertFalse(FlagService.is_enabled('demo_feature', org_id=5, user_id=9))

    def test_unknown_flag_is_false_and_cached(self):
        self.assertFalse(FlagService.is_enabled('nope', org_id=1))
        with _QueryCounter(db.engine) as counter:
            self.assertFalse(FlagService.is_enabled('nope', org_id=1))
        self.assertEqual(counter.count, 0)

    def test_ensure_defaults_invalidates_cache(self):
        self.assertFalse(FlagService.is_enabled('geo_map'))
        FlagService.ensure_defaults()
        self.assertTrue(FlagService.is_enabled('geo_map'))


if __name__ == '__main__':
    unittest.main()
