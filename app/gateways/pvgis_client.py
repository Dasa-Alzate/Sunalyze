"""Adaptador de PVGIS (irradiancia horaria) con cache en proceso.

Unica frontera con la API externa: detras de esta interfaz el dominio es
mockeable en tests y el cache puede migrar a Redis sin tocar los services.
"""

import logging
import threading
import pvlib

logger = logging.getLogger(__name__)


class PvgisClient:

    _CACHE = {}
    _CACHE_MAX_SIZE = 50
    _LOCK = threading.Lock()

    @classmethod
    def get_hourly(cls, lat, lon, start_year, end_year):
        cache_key = f'{lat:.4f}_{lon:.4f}_{start_year}_{end_year}'

        with cls._LOCK:
            if cache_key in cls._CACHE:
                logger.debug('Cache hit para: %s', cache_key)
                return cls._CACHE[cache_key]

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

        with cls._LOCK:
            if len(cls._CACHE) >= cls._CACHE_MAX_SIZE and cache_key not in cls._CACHE:
                cls._CACHE.pop(next(iter(cls._CACHE)), None)
            cls._CACHE[cache_key] = (df, meta)
            logger.debug('Datos guardados en cache. Tamaño actual: %s', len(cls._CACHE))
        return df, meta

    @classmethod
    def cache_size(cls):
        return len(cls._CACHE)
