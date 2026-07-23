
import unittest

from sqlalchemy import event

from app import create_app
from app.extensions import db
from app.models.catalog import Catalog
from app.models.organization import Organization
from app.models.panel import Panel
from app.models.inverter import Inverter
from app.models.battery import Battery
from app.models.wire import Wire
from app.services.catalog_service import CatalogService


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


class _QueryCounter:

    def __init__(self, engine):
        self.engine = engine
        self.statements = []

    def __enter__(self):
        event.listen(self.engine, 'before_cursor_execute', self._record)
        return self

    def __exit__(self, *exc):
        event.remove(self.engine, 'before_cursor_execute', self._record)

    def _record(self, conn, cursor, statement, parameters, context, executemany):
        self.statements.append(statement)

    @property
    def count(self):
        return len(self.statements)


class CatalogCountsTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.org = Organization(nombre='Org', type='BUSINESS', plan='pro')
        db.session.add(self.org)
        db.session.flush()
        self.catalogs = []
        for i in range(5):
            c = Catalog(nombre=f'Cat {i}', org_id=self.org.id)
            db.session.add(c)
            db.session.flush()
            self.catalogs.append(c)
        self._seed_items(self.catalogs[0], panels=3, inverters=2, batteries=1, wires=4)
        self._seed_items(self.catalogs[1], panels=1)
        self._seed_items(self.catalogs[2], batteries=2, wires=1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_items(self, catalog, panels=0, inverters=0, batteries=0, wires=0):
        for i in range(panels):
            db.session.add(Panel(nombre=f'P-{catalog.id}-{i}', power=400.0, voc=37.0,
                                 vmp=31.0, imp=13.0, catalog_id=catalog.id))
        for i in range(inverters):
            db.session.add(Inverter(nombre=f'I-{catalog.id}-{i}', power=5000.0,
                                    vmax=600.0, catalog_id=catalog.id))
        for i in range(batteries):
            db.session.add(Battery(nombre=f'B-{catalog.id}-{i}', capacity_kwh=10.0,
                                   power_kw=5.0, voltage=48.0, catalog_id=catalog.id))
        for i in range(wires):
            db.session.add(Wire(seccion=6.0, corriente=40.0 + i, tipo='DC',
                                material='Cu', no_conductores=2, catalog_id=catalog.id))
        db.session.flush()

    def _legacy_counts(self, catalog_id):
        return {
            'panels': Panel.query.filter_by(catalog_id=catalog_id).count(),
            'inverters': Inverter.query.filter_by(catalog_id=catalog_id).count(),
            'batteries': Battery.query.filter_by(catalog_id=catalog_id).count(),
            'wires': Wire.query.filter_by(catalog_id=catalog_id).count(),
        }

    def test_counts_map_matches_per_catalog_counts(self):
        ids = [c.id for c in self.catalogs]
        batched = CatalogService.counts_map(ids)
        for cid in ids:
            self.assertEqual(batched[cid], self._legacy_counts(cid))

    def test_counts_map_empty_input(self):
        self.assertEqual(CatalogService.counts_map([]), {})

    def test_library_output_shape_and_values(self):
        rows = CatalogService.library(self.org.id)
        self.assertEqual(len(rows), 5)
        by_id = {r['id']: r for r in rows}
        self.assertEqual(by_id[self.catalogs[0].id]['counts'],
                         {'panels': 3, 'inverters': 2, 'batteries': 1, 'wires': 4})
        self.assertEqual(by_id[self.catalogs[1].id]['counts'],
                         {'panels': 1, 'inverters': 0, 'batteries': 0, 'wires': 0})
        self.assertEqual(by_id[self.catalogs[3].id]['counts'],
                         {'panels': 0, 'inverters': 0, 'batteries': 0, 'wires': 0})
        for row in rows:
            self.assertIn('own', row)
            self.assertIn('subscribed', row)
            self.assertTrue(row['own'])
            self.assertFalse(row['subscribed'])

    def test_counts_map_issues_at_most_four_queries(self):
        ids = [c.id for c in self.catalogs]
        with _QueryCounter(db.engine) as counter:
            CatalogService.counts_map(ids)
        self.assertLessEqual(counter.count, 4)

    def test_library_query_count_independent_of_catalog_number(self):
        db.session.expire_all()
        with _QueryCounter(db.engine) as counter:
            CatalogService.library(self.org.id)
        self.assertLessEqual(counter.count, 8)

    def test_marketplace_counts(self):
        public = Catalog(nombre='Oficial', org_id=None, is_official=True, is_active=True)
        db.session.add(public)
        db.session.flush()
        self._seed_items(public, panels=2, inverters=1)
        db.session.commit()
        rows = CatalogService.marketplace(self.org.id)
        match = [r for r in rows if r['id'] == public.id]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]['counts'],
                         {'panels': 2, 'inverters': 1, 'batteries': 0, 'wires': 0})


if __name__ == '__main__':
    unittest.main()
