

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
