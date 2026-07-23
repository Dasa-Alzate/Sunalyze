
from flask import request

DEFAULT_LOCALE = 'es'
SUPPORTED_LOCALES = ('es', 'en')


def normalize_locale(value):
    if not value:
        return None
    lang = str(value).strip().lower().replace('_', '-').split('-')[0]
    return lang if lang in SUPPORTED_LOCALES else None


def resolve_locale(user=None):
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
