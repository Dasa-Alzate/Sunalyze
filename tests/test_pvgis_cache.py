
import unittest
from unittest.mock import patch

import pandas as pd

from app import create_app
from app.gateways.pvgis_client import PvgisClient


def _make_app():
    app = create_app({'SQLALCHEMY_DATABASE_URI': 'sqlite://', 'TESTING': True})
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite://', WTF_CSRF_ENABLED=False)
    return app


def _fake_pvgis_df():
    idx = pd.date_range('2020-01-01', periods=24, freq='h')
    n = len(idx)
    df = pd.DataFrame(
        {
            'poa_direct': [400.0] * n,
            'poa_sky_diffuse': [100.0] * n,
            'poa_ground_diffuse': [20.0] * n,
            'temp_air': [20.0] * n,
        },
        index=idx,
    )
    meta = {'inputs': {'location': {'elevation': 100.0}}}
    return df, meta


class PvgisCacheTest(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_second_call_served_from_cache(self):
        with patch('app.gateways.pvgis_client.pvlib.iotools.get_pvgis_hourly',
                   return_value=_fake_pvgis_df()) as fetch:
            df1, meta1 = PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
            df2, meta2 = PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
        self.assertEqual(fetch.call_count, 1)
        pd.testing.assert_frame_equal(df1, df2)
        self.assertEqual(meta1, meta2)

    def test_different_params_fetch_separately(self):
        with patch('app.gateways.pvgis_client.pvlib.iotools.get_pvgis_hourly',
                   return_value=_fake_pvgis_df()) as fetch:
            PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
            PvgisClient.get_hourly(41.3874, 2.1686, 2019, 2020)
            PvgisClient.get_hourly(40.4168, -3.7038, 2018, 2020)
        self.assertEqual(fetch.call_count, 3)

    def test_network_failure_propagates_and_caches_nothing(self):
        with patch('app.gateways.pvgis_client.pvlib.iotools.get_pvgis_hourly',
                   side_effect=OSError('PVGIS down')) as fetch:
            with self.assertRaises(OSError):
                PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
        self.assertEqual(fetch.call_count, 1)
        with patch('app.gateways.pvgis_client.pvlib.iotools.get_pvgis_hourly',
                   return_value=_fake_pvgis_df()) as retry:
            PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
        self.assertEqual(retry.call_count, 1)

    def test_cache_key_stable_per_params(self):
        key_a = PvgisClient._cache_key(40.4168, -3.7038, 2019, 2020)
        key_b = PvgisClient._cache_key(40.41680, -3.70380, 2019, 2020)
        key_c = PvgisClient._cache_key(40.4169, -3.7038, 2019, 2020)
        self.assertEqual(key_a, key_b)
        self.assertNotEqual(key_a, key_c)

    def test_cache_size_counts_pvgis_entries(self):
        self.assertEqual(PvgisClient.cache_size(), 0)
        with patch('app.gateways.pvgis_client.pvlib.iotools.get_pvgis_hourly',
                   return_value=_fake_pvgis_df()):
            PvgisClient.get_hourly(40.4168, -3.7038, 2019, 2020)
        self.assertEqual(PvgisClient.cache_size(), 1)


if __name__ == '__main__':
    unittest.main()
