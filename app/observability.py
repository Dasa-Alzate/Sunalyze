"""Inicialización opcional de Sentry, activada solo por SENTRY_DSN.

Sigue el patrón del repo para dependencias opcionales (boto3/rq): el import
de sentry_sdk es perezoso y solo ocurre si hay DSN configurado, de modo que
sin DSN la app arranca aunque el paquete no esté instalado y no se produce
ningún efecto secundario. send_default_pii queda en False (RGPD): los eventos
no llevan IPs, cookies ni datos personales del request.
"""


def init_sentry(app):
    dsn = app.config.get('SENTRY_DSN')
    if not dsn:
        return
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=dsn,
        integrations=[FlaskIntegration()],
        environment=app.config['SENTRY_ENVIRONMENT'],
        traces_sample_rate=app.config['SENTRY_TRACES_SAMPLE_RATE'],
        send_default_pii=False,
    )
