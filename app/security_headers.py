
from flask import jsonify
from flask_wtf.csrf import CSRFError, generate_csrf

from app.extensions import csrf, limiter

CSP_DIRECTIVES = {
    'default-src': "'self'",
    'script-src': "'self' 'sha256-W3VlYOkiCmZzATwlGWce86qt1r5NXrQlWFWN1C8uX/E='",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
    'font-src': "'self' https://fonts.gstatic.com",
    'img-src': "'self' data: https://*.tile.openstreetmap.org",
    'connect-src': "'self' https://nominatim.openstreetmap.org",
    'frame-src': "https://www.openstreetmap.org https://openstreetmap.org",
    'base-uri': "'self'",
    'form-action': "'self'",
    'object-src': "'none'",
    'frame-ancestors': "'none'",
}


def _content_security_policy():
    return '; '.join(f'{k} {v}' for k, v in CSP_DIRECTIVES.items())


def register_security(app):
    app.config.setdefault('WTF_CSRF_TIME_LIMIT', None)
    app.config.setdefault('WTF_CSRF_SAMESITE', 'Lax')

    csrf.init_app(app)
    limiter.init_app(app)

    is_prod = app.config.get('IS_PRODUCTION', False)
    csp = _content_security_policy()

    @app.after_request
    def apply_security(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Content-Security-Policy', csp)
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        if is_prod:
            response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
        response.set_cookie(
            'csrf_token', generate_csrf(),
            secure=is_prod, httponly=False, samesite='Lax',
        )
        return response

    @app.errorhandler(CSRFError)
    def handle_csrf_error(err):
        return jsonify({'error': 'Token CSRF inválido o ausente. Recarga la página.'}), 403
