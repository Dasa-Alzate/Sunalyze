"""Resolucion del locale activo por precedencia, con stdlib + Flask.

No introduce librerias de i18n en el backend: la traduccion de la UI vive en el
cliente. Aqui solo se decide que locale aplica a una peticion (para emails y para
exponerlo al frontend) por precedencia: usuario > Accept-Language > default.
"""

from flask import request

DEFAULT_LOCALE = 'es'
SUPPORTED_LOCALES = ('es', 'en')


def normalize_locale(value):
    """Reduce un locale a su idioma soportado (`es-ES` -> `es`) o None."""
    if not value:
        return None
    lang = str(value).strip().lower().replace('_', '-').split('-')[0]
    return lang if lang in SUPPORTED_LOCALES else None


def resolve_locale(user=None):
    """Locale activo por precedencia: user.locale > Accept-Language > default."""
    from_user = normalize_locale(getattr(user, 'locale', None)) if user else None
    if from_user:
        return from_user
    from_header = _from_accept_language()
    if from_header:
        return from_header
    return DEFAULT_LOCALE


def _from_accept_language():
    if not request:
        return None
    try:
        best = request.accept_languages.best_match(SUPPORTED_LOCALES)
    except RuntimeError:
        return None
    return normalize_locale(best)
