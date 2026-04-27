"""Lectura y aplicación de migraciones Alembic desde el portal.

`status()`/`history()` solo leen; `do_upgrade()` ejecuta upgrade-to-head y
devuelve (antes, después) para auditar. El downgrade NO se expone por la web.
"""

from flask import current_app
from flask_migrate import upgrade as _upgrade
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext

from app.extensions import db


def _config():
    return current_app.extensions['migrate'].migrate.get_config()


def _script():
    return ScriptDirectory.from_config(_config())


def current_revision():
    with db.engine.connect() as conn:
        return MigrationContext.configure(conn).get_current_revision()


def status():
    script = _script()
    current = current_revision()
    head = script.get_current_head()
    return {'current': current, 'head': head, 'up_to_date': current == head}


def history():
    script = _script()
    current = current_revision()
    applied = set()
    if current:
        for rev in script.iterate_revisions(current, 'base'):
            applied.add(rev.revision)
    rows = []
    for rev in script.walk_revisions():
        rows.append({
            'revision': rev.revision,
            'down_revision': rev.down_revision,
            'message': (rev.doc or '').strip().splitlines()[0] if rev.doc else '',
            'is_current': rev.revision == current,
            'is_applied': rev.revision in applied,
        })
    return rows


def do_upgrade():
    before = current_revision()
    _upgrade()
    after = current_revision()
    return before, after
