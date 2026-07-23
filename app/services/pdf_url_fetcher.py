
import mimetypes
import os
from urllib.parse import urlparse, unquote
from urllib.request import url2pathname

from flask import current_app


def allowed_root():
    return os.path.realpath(current_app.instance_path)


def restricted_url_fetcher(url):
    from weasyprint.urls import default_url_fetcher

    parsed = urlparse(url)
    scheme = (parsed.scheme or '').lower()

    if scheme == 'data':
        return default_url_fetcher(url)

    if scheme in ('', 'file'):
        raw_path = url2pathname(unquote(parsed.path))
        root = allowed_root()
        if os.path.isabs(raw_path):
            real = os.path.realpath(raw_path)
        else:
            real = os.path.realpath(os.path.join(root, raw_path))
        if (real == root or real.startswith(root + os.sep)) and os.path.isfile(real):
            mime, _ = mimetypes.guess_type(real)
            return {
                'file_obj': open(real, 'rb'),
                'mime_type': mime or 'application/octet-stream',
            }
        raise ValueError('Recurso local fuera del arbol permitido.')

    raise ValueError(f'Esquema de recurso no permitido en el PDF: {scheme or "relativo"}')
