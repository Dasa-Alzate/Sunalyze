"""Perfiles de presentación por país (code-as-config) y resolución de jurisdicción.

Cada país mapea a `{locale, currency, page_size}`. La jurisdicción de una plantilla deriva de
su `country`; `locale` y `currency` explícitos en la plantilla son override. No depende de
Flask ni de babel: el formateo de números/moneda usa solo stdlib (ver `filters.py`).
"""

DEFAULT_COUNTRY = 'ES'

COUNTRY_PROFILES = {
    'ES': {'locale': 'es', 'currency': 'EUR', 'page_size': 'A4'},
    'FR': {'locale': 'fr', 'currency': 'EUR', 'page_size': 'A4'},
    'DE': {'locale': 'de', 'currency': 'EUR', 'page_size': 'A4'},
    'IT': {'locale': 'it', 'currency': 'EUR', 'page_size': 'A4'},
    'PT': {'locale': 'pt', 'currency': 'EUR', 'page_size': 'A4'},
    'GB': {'locale': 'en', 'currency': 'GBP', 'page_size': 'A4'},
    'US': {'locale': 'en', 'currency': 'USD', 'page_size': 'Letter'},
    'MX': {'locale': 'es', 'currency': 'MXN', 'page_size': 'Letter'},
    'CO': {'locale': 'es', 'currency': 'COP', 'page_size': 'Letter'},
    'CL': {'locale': 'es', 'currency': 'CLP', 'page_size': 'Letter'},
}

CURRENCY_SYMBOLS = {
    'EUR': '€',
    'USD': '$',
    'GBP': '£',
    'MXN': '$',
    'COP': '$',
    'CLP': '$',
}

CURRENCY_SYMBOL_AFTER = {'EUR'}


def country_profile(country):
    """Perfil de presentación de un país (default ES si desconocido o vacío)."""
    if not country:
        return dict(COUNTRY_PROFILES[DEFAULT_COUNTRY])
    return dict(COUNTRY_PROFILES.get(country.strip().upper(), COUNTRY_PROFILES[DEFAULT_COUNTRY]))


def resolve_jurisdiction(country=None, locale=None, currency=None):
    """Resuelve la presentación efectiva: perfil del país con overrides explícitos.

    Devuelve `{locale, currency, page_size}`. `locale`/`currency` no vacíos sobreescriben el
    valor derivado del país.
    """
    profile = country_profile(country)
    if locale:
        profile['locale'] = locale.strip()
    if currency:
        profile['currency'] = currency.strip().upper()
    return profile
