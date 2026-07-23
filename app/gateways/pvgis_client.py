
import logging

import pvlib

from app.extensions import cache

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60 * 60 * 24 * 30
_KEY_PREFIX = 'pvgis:hourly:'


class PvgisClient:

    @staticmethod
    def _cache_key(lat, lon, start_year, end_year):
        return f'{_KEY_PREFIX}{lat:.4f}_{lon:.4f}_{start_year}_{end_year}'

    @classmethod
    def get_hourly(cls, lat, lon, start_year, end_year):
        cache_key = cls._cache_key(lat, lon, start_year, end_year)

        hit = cache.get(cache_key)
        if hit is not None:
            logger.debug('Cache hit para: %s', cache_key)
            return hit

        logger.debug('Cache miss, llamando a PVGIS para: %s', cache_key)

        df, meta = pvlib.iotools.get_pvgis_hourly(
            latitude=lat,
            longitude=lon,
            start=start_year,
            end=end_year,
            raddatabase='PVGIS-SARAH3',
            surface_tilt=0,
            surface_azimuth=180,
            components=True,
            usehorizon=True,
            outputformat='json',
        )

        cache.set(cache_key, (df, meta), timeout=CACHE_TTL_SECONDS)
        logger.debug('Datos PVGIS guardados en cache para: %s', cache_key)
        return df, meta

    @classmethod
    def cache_size(cls):
        entries = getattr(cache.cache, '_cache', None)
        if entries is None:
            return 0
        return sum(1 for key in entries if _KEY_PREFIX in key)
