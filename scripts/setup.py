"""Prepara Sunalyze para desarrollo local en Windows, macOS o Linux.

    python scripts/setup.py            instala y deja la app lista para arrancar
    python scripts/setup.py --check    diagnostica sin tocar nada
    python scripts/setup.py --reset    rehace la base de datos desde cero

No necesita nada instalado salvo Python 3.12+. Crea el entorno virtual, instala
las dependencias, escribe el .env, migra la base de datos, siembra la cuenta de
prueba y comprueba que el login funciona de verdad.
"""

import argparse
import os
import platform
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = ROOT / '.venv'
ENV_FILE = ROOT / '.env'
ENV_EXAMPLE = ROOT / '.env.example'
FLASKENV = ROOT / '.flaskenv'
FRONTEND = ROOT / 'frontend'

MIN_PYTHON = (3, 12)
DEMO_EMAIL = 'sunalize_test@sunalize.com'
DEMO_PASSWORD = 'test123'
IS_WINDOWS = os.name == 'nt'
SYSTEM = platform.system()

GTK_HINT = {
    'Windows': 'WeasyPrint necesita GTK en Windows nativo. Lo más rápido es usar Docker\n'
               '     (docker compose --env-file .env.docker up -d --build) o WSL2 con Ubuntu.',
    'Darwin': 'Instala las librerías de PDF con:  brew install pango libffi',
    'Linux': 'Instala las librerías de PDF con:\n'
             '     sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core',
}

MYSQL_HINT = {
    'Windows': 'Usa el conector puro de Python: en DATABASE_URL escribe mysql+pymysql://...',
    'Darwin': 'Instala el cliente de MySQL con:  brew install mysql-client pkg-config',
    'Linux': 'Instala el cliente de MySQL con:\n'
             '     sudo apt-get install -y build-essential pkg-config default-libmysqlclient-dev',
}

failures = []


def out(text=''):
    print(text, flush=True)


def step(text):
    out('\n== %s' % text)


def ok(text):
    out('   [ok] %s' % text)


def warn(text):
    out('   [!]  %s' % text)


def bad(text):
    out('   [x]  %s' % text)
    failures.append(text)


def hint(text):
    out('        %s' % text)


def venv_python():
    if IS_WINDOWS:
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'


def interpreter():
    python = venv_python()
    return str(python) if python.exists() else sys.executable


def run(args, capture=True, check=False):
    return subprocess.run(
        args, cwd=str(ROOT), capture_output=capture, text=True,
        encoding='utf-8', errors='replace', check=check,
    )


def run_python(args, capture=True):
    return run([interpreter()] + args, capture=capture)


def run_flask(args, capture=True):
    return run([interpreter(), '-m', 'flask'] + args, capture=capture)


def explain(output):
    blob = (output or '').lower()
    if 'libgobject' in blob or 'cairo' in blob or 'pango' in blob or 'weasyprint' in blob:
        hint(GTK_HINT.get(SYSTEM, GTK_HINT['Linux']))
        return True
    if 'mysqlclient' in blob or 'mysql_config' in blob or 'mariadb_config' in blob:
        hint(MYSQL_HINT.get(SYSTEM, MYSQL_HINT['Linux']))
        return True
    if 'multiple head revisions' in blob:
        hint('El grafo de migraciones tiene dos ramas. Une los heads con:')
        hint('  flask db heads   y luego   flask db merge -m "merge heads" <rev-a> <rev-b>')
        return True
    if 'access denied' in blob:
        hint('La base de datos rechaza las credenciales de DATABASE_URL (.env).')
        hint('El usuario y la base tienen que existir ya; .env sólo dice cómo conectarse.')
        hint('Si no quieres pelearte con MySQL, usa:  DATABASE_URL=sqlite:///sunalyze.db')
        return True
    if "can't connect" in blob or 'connection refused' in blob:
        hint('No hay ninguna base de datos escuchando en la dirección de DATABASE_URL.')
        hint('Para arrancar sin instalar nada:  DATABASE_URL=sqlite:///sunalyze.db')
        return True
    if 'no such table' in blob:
        hint('Faltan las tablas. Ejecuta:  python scripts/setup.py')
        return True
    return False


def tail(output, lines=6):
    text = (output or '').strip().splitlines()
    for line in text[-lines:]:
        hint(line)


def check_python():
    step('Python')
    if sys.version_info < MIN_PYTHON:
        bad('Tienes Python %d.%d y hacen falta %d.%d o superior.'
            % (sys.version_info[0], sys.version_info[1], MIN_PYTHON[0], MIN_PYTHON[1]))
        hint('Descárgalo en https://www.python.org/downloads/')
        return False
    ok('Python %d.%d.%d en %s' % (sys.version_info[0], sys.version_info[1],
                                  sys.version_info[2], SYSTEM))
    return True


def ensure_venv():
    step('Entorno virtual (.venv)')
    if venv_python().exists():
        ok('Ya existe')
        return True
    result = run([sys.executable, '-m', 'venv', str(VENV_DIR)])
    if result.returncode != 0 or not venv_python().exists():
        bad('No se pudo crear el entorno virtual')
        tail(result.stderr)
        if SYSTEM == 'Linux':
            hint('En Debian/Ubuntu puede faltar el paquete:  sudo apt-get install -y python3-venv')
        return False
    ok('Creado en .venv')
    return True


def install_requirements():
    step('Dependencias de Python')
    result = run([interpreter(), '-m', 'pip', 'install', '--upgrade', 'pip', '--quiet'])
    result = run([interpreter(), '-m', 'pip', 'install', '-r',
                  str(ROOT / 'requirements.txt'), '--quiet'])
    if result.returncode != 0:
        bad('Falló la instalación de dependencias')
        tail((result.stdout or '') + (result.stderr or ''))
        explain((result.stdout or '') + (result.stderr or ''))
        return False
    ok('Instaladas')
    return True


def ensure_env():
    step('Configuración (.env)')
    if ENV_FILE.exists():
        ok('Ya existe (no lo toco)')
    else:
        if not ENV_EXAMPLE.exists():
            bad('Falta .env.example, no puedo generar la configuración')
            return False
        shutil.copyfile(str(ENV_EXAMPLE), str(ENV_FILE))
        with open(str(ENV_FILE), 'a', encoding='utf-8') as handle:
            handle.write('\nSECRET_KEY=%s\n' % secrets.token_hex(32))
        ok('Creado desde .env.example (SQLite, sin configurar nada)')
        ok('SECRET_KEY generada (tu sesion sobrevive a los reinicios)')
    if not FLASKENV.exists():
        FLASKENV.write_text('FLASK_APP=run\n', encoding='utf-8')
        ok('Creado .flaskenv (ya no necesitas export/set FLASK_APP)')
    return True


def database_url():
    result = run_python(['-c',
        'from run import app; print(app.config["SQLALCHEMY_DATABASE_URI"])'])
    if result.returncode != 0:
        return None, (result.stdout or '') + (result.stderr or '')
    line = [x for x in (result.stdout or '').splitlines() if '://' in x]
    return (line[-1].strip() if line else None), ''


def reset_database():
    step('Borrando la base de datos anterior (--reset)')
    url, _ = database_url()
    if url and url.startswith('sqlite:///'):
        name = url[len('sqlite:///'):]
        for candidate in (ROOT / 'instance' / name, Path(name)):
            try:
                if candidate.exists():
                    candidate.unlink()
                    ok('Borrado %s' % candidate)
            except Exception:
                warn('No pude borrar %s' % candidate)
    else:
        warn('DATABASE_URL no es SQLite; no borro nada por seguridad.')
        hint('Vacía la base a mano si de verdad quieres empezar de cero.')
    return True


def migrate():
    step('Base de datos')
    url, error = database_url()
    if url is None:
        bad('La aplicación no arranca')
        tail(error)
        explain(error)
        return False
    ok('Conectando a %s' % url)
    result = run_flask(['db', 'upgrade'])
    blob = (result.stdout or '') + (result.stderr or '')
    if result.returncode != 0:
        bad('Fallaron las migraciones')
        tail(blob)
        explain(blob)
        return False
    ok('Migraciones aplicadas')
    return True


def seed():
    step('Cuenta de prueba')
    result = run_flask(['seed', 'demo'])
    blob = (result.stdout or '') + (result.stderr or '')
    if result.returncode != 0 or 'Aborted' in blob:
        bad('No se pudo sembrar la cuenta de prueba')
        tail(blob)
        if 'Aborted' in blob:
            hint('El seed se niega a correr con FLASK_ENV=production.')
            hint('Quita esa línea del .env o usa ALLOW_SEED_DEMO=1.')
        explain(blob)
        return False
    ok('Lista: %s / %s' % (DEMO_EMAIL, DEMO_PASSWORD))
    return True


def verify_login():
    step('Comprobación real del login')
    code = (
        'from run import app\n'
        'from app.models.user import User\n'
        'with app.app_context():\n'
        '    u = User.query.filter_by(email=%r).first()\n'
        '    print("USER", bool(u))\n'
        '    print("PASS", bool(u and u.check_password(%r)))\n'
    ) % (DEMO_EMAIL, DEMO_PASSWORD)
    result = run_python(['-c', code])
    blob = (result.stdout or '') + (result.stderr or '')
    if 'USER True' not in blob:
        bad('El usuario de prueba no está en la base que lee la aplicación')
        tail(blob)
        return False
    if 'PASS True' not in blob:
        bad('El usuario existe pero la contraseña no es la esperada')
        hint('Resetéala con:  flask shell  ->  u.set_password("%s")' % DEMO_PASSWORD)
        return False
    ok('El usuario existe y la contraseña valida')
    return True


def build_frontend():
    step('Frontend')
    npm = shutil.which('npm')
    if not npm:
        warn('npm no está instalado: la interfaz no se compilará')
        hint('La API funciona igual. Para la interfaz instala Node 18+ desde https://nodejs.org')
        return True
    if (FRONTEND / 'dist' / 'index.html').exists():
        ok('Ya compilado (borra frontend/dist para rehacerlo)')
        return True
    result = subprocess.run([npm, 'install'], cwd=str(FRONTEND),
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        warn('npm install falló; la API funcionará pero no la interfaz')
        tail((result.stdout or '') + (result.stderr or ''))
        return True
    result = subprocess.run([npm, 'run', 'build'], cwd=str(FRONTEND),
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        warn('npm run build falló; la API funcionará pero no la interfaz')
        tail((result.stdout or '') + (result.stderr or ''))
        return True
    ok('Compilado en frontend/dist')
    return True


def catalog_report():
    code = (
        'from run import app\n'
        'from app.models.catalog import Catalog\n'
        'with app.app_context():\n'
        '    total = Catalog.query.count()\n'
        '    off = Catalog.query.filter_by(is_active=False).count()\n'
        '    print("CATALOGS", total, off)\n'
    )
    result = run_python(['-c', code])
    for line in (result.stdout or '').splitlines():
        if line.startswith('CATALOGS'):
            parts = line.split()
            return int(parts[1]), int(parts[2])
    return None, None


def activate_catalogs():
    step('Activando catálogos importados')
    code = (
        'from run import app\n'
        'from app.extensions import db\n'
        'from app.models.catalog import Catalog\n'
        'from app.models.organization import Organization\n'
        'from app.services.catalog_service import CatalogService\n'
        'with app.app_context():\n'
        '    n = Catalog.query.filter_by(is_active=False).update({Catalog.is_active: True})\n'
        '    db.session.commit()\n'
        '    subs = 0\n'
        '    ids = [c.id for c in Catalog.query.filter_by(org_id=None).all()]\n'
        '    for org in Organization.query.all():\n'
        '        for cid in ids:\n'
        '            try:\n'
        '                CatalogService.subscribe(org.id, cid)\n'
        '                subs += 1\n'
        '            except Exception:\n'
        '                pass\n'
        '    db.session.commit()\n'
        '    print("ACTIVATED", n, subs)\n'
    )
    result = run_python(['-c', code])
    blob = (result.stdout or '') + (result.stderr or '')
    for line in (result.stdout or '').splitlines():
        if line.startswith('ACTIVATED'):
            parts = line.split()
            ok('%s catálogos activados, %s suscripciones aseguradas' % (parts[1], parts[2]))
            return True
    bad('No se pudieron activar los catálogos')
    tail(blob)
    return False


def doctor():
    out('Diagnóstico de Sunalyze (no modifica nada)')
    check_python()

    step('Entorno virtual')
    if venv_python().exists():
        ok('.venv existe')
    else:
        bad('.venv no existe')
        hint('Ejecuta:  python scripts/setup.py')

    step('Configuración')
    if ENV_FILE.exists():
        ok('.env existe')
    else:
        bad('.env no existe')
        hint('Ejecuta:  python scripts/setup.py')
    if FLASKENV.exists():
        ok('.flaskenv existe (FLASK_APP resuelto solo)')
    else:
        warn('.flaskenv no existe: tendrás que definir FLASK_APP a mano')

    step('Aplicación y base de datos')
    url, error = database_url()
    if url is None:
        bad('La aplicación no arranca')
        tail(error)
        explain(error)
    else:
        ok('DATABASE_URL en uso: %s' % url)
        result = run_flask(['db', 'current'])
        blob = (result.stdout or '') + (result.stderr or '')
        if result.returncode != 0:
            bad('No se puede leer el estado de las migraciones')
            tail(blob)
            explain(blob)
        else:
            found = re.findall(r'\b[0-9a-f]{12}\b', blob)
            if found:
                ok('Migraciones en: %s' % found[-1])
            else:
                warn('No hay ninguna migracion aplicada todavia')
                hint('Ejecuta:  python scripts/setup.py')

        verify_login()

        step('Catálogos de equipos')
        total, off = catalog_report()
        if total is None:
            warn('No se pudo consultar el catálogo')
        elif off:
            warn('%d de %d catálogos están DESACTIVADOS' % (off, total))
            hint('Sus equipos no salen ni en la vista ni en el marketplace. Es el')
            hint('comportamiento por defecto del scraper, no un error.')
            hint('Para activarlos:  python scripts/setup.py --activate-catalogs')
        else:
            ok('Los %d catálogos están activos' % total)

    summary()


def summary():
    out('')
    if failures:
        out('Resultado: %d problema(s).' % len(failures))
        for item in failures:
            out('  - %s' % item)
        return 1
    out('Resultado: todo correcto.')
    return 0


def final_instructions():
    out('')
    out('=' * 66)
    out('  Sunalyze está listo.')
    out('=' * 66)
    out('')
    out('  Arranca la aplicación:')
    if IS_WINDOWS:
        out('      .venv\\Scripts\\activate')
    else:
        out('      source .venv/bin/activate')
    port = '5001' if SYSTEM == 'Darwin' else '5000'
    out('      flask run -p %s' % port)
    if SYSTEM == 'Darwin':
        out('      (en macOS el puerto 5000 lo ocupa AirPlay, por eso el 5001)')
    out('')
    out('  Abre http://localhost:%s y entra con:' % port)
    out('      %s' % DEMO_EMAIL)
    out('      %s' % DEMO_PASSWORD)
    out('')
    out('  Si algo va mal:  python scripts/setup.py --check')
    out('')


def setup(args):
    out('Preparando Sunalyze para desarrollo local (%s)' % SYSTEM)
    if not check_python():
        return summary()
    if not ensure_venv():
        return summary()
    if not install_requirements():
        return summary()
    if not ensure_env():
        return summary()
    if args.reset:
        reset_database()
    if not migrate():
        return summary()
    if not seed():
        return summary()
    if not verify_login():
        return summary()
    build_frontend()

    total, off = catalog_report()
    if off:
        step('Aviso sobre catálogos')
        warn('%d de %d catálogos están desactivados y sus equipos no se ven.' % (off, total))
        hint('Actívalos con:  python scripts/setup.py --activate-catalogs')

    code = summary()
    if code == 0:
        final_instructions()
    return code


def main():
    parser = argparse.ArgumentParser(
        description='Prepara Sunalyze para desarrollo local.')
    parser.add_argument('--check', action='store_true',
                        help='sólo diagnostica, no modifica nada')
    parser.add_argument('--reset', action='store_true',
                        help='borra la base de datos SQLite antes de migrar')
    parser.add_argument('--activate-catalogs', action='store_true',
                        dest='activate_catalogs',
                        help='activa los catálogos importados y suscribe a las organizaciones')
    args = parser.parse_args()

    if args.check:
        doctor()
        return 1 if failures else 0
    if args.activate_catalogs:
        activate_catalogs()
        return summary()
    return setup(args)


if __name__ == '__main__':
    sys.exit(main())
