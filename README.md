# Sunalyze

Sunalyze es una aplicación Flask para el análisis y dimensionamiento de sistemas fotovoltaicos. Utiliza datos de irradiancia de PVGIS para calcular requerimientos de paneles solares e inversores compatibles.

## Características

- Cálculo de irradiancia óptima según ubicación (latitud/longitud)
- Dimensionamiento de campos fotovoltaicos
- Selección de inversores compatibles
- Cálculo de pérdidas por temperatura, suciedad y cableado
- Generación de memorias técnicas y diagramas funcionales
- CRUD de paneles, inversores y cables

## Requisitos

- Python 3.10+
- MySQL 8.0+

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd Sunalyze
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Compilar el frontend (React):
```bash
cd frontend
npm install
npm run build
cd ..
```
Esto genera `frontend/dist/`, que Flask sirve en la raíz. **`frontend/dist/` NO se
versiona** (está en `.gitignore`): es un artefacto de build. Hay que compilarlo
antes de servir con Flask — en local tras clonar, y como **paso de build en el
despliegue**. Vuelve a ejecutar `npm run build` cada vez que cambies el frontend.

> **Despliegue:** como el `dist/` no viaja en el repo, el pipeline debe ejecutar
> `cd frontend && npm install && npm run build` (requiere Node) antes de arrancar
> Gunicorn. Si tu plataforma sólo corre el provider de Python, añade ese paso de
> Node al build o publica el `dist/` por otra vía. Si Flask no encuentra
> `frontend/dist/index.html`, la raíz muestra un aviso con instrucciones en vez de fallar.

> Los assets Tailwind/DaisyUI del backend (`app/static/css/output.css`) ya sólo
> visten las plantillas PDF (memoria técnica y diagrama). Si las modificas,
> recompílalos con `npm install && npm run build` en la raíz del proyecto.

5. Configurar variables de entorno:
```bash
export SECRET_KEY='tu-clave-secreta'
export DATABASE_URL='mysql+pymysql://usuario:password@localhost/sunalyze'
```
En desarrollo ambas son opcionales (la app usa valores por defecto). En producción (`FLASK_ENV=production`) **`SECRET_KEY` y `DATABASE_URL` son obligatorias**: la aplicación lanza un error al iniciar si no están definidas.

6. Configurar la base de datos:
```bash
python init_db.py
```

> **Arranque rápido sin MySQL.** Para desarrollo puedes usar SQLite sin instalar
> nada: `export DATABASE_URL="sqlite:///$PWD/sunalyze_dev.db"` antes de
> `python init_db.py` y `python run.py`. El catálogo (`data/database.json`) se
> carga igual.

> **PDF de la memoria (WeasyPrint).** La generación del PDF necesita las
> librerías de sistema de Pango/cairo. En macOS: `brew install pango`; en
> Debian/Ubuntu: `libpango-1.0-0 libpangoft2-1.0-0` (ya declaradas en
> `railpack.json`). El resto de la app arranca aunque falten — el import de
> WeasyPrint es diferido y sólo se ejerce al generar el PDF.

## Ejecución

### Producción / build servido por Flask
```bash
python run.py
```
La aplicación (SPA de React + API) estará disponible en `http://localhost:5000`.

### Desarrollo con recarga en caliente
Arranca el backend y el servidor de Vite en dos terminales:
```bash
python run.py                 # API Flask en :5000
cd frontend && npm run dev    # SPA con HMR en :5173 (proxy /api → :5000)
```
Abre `http://localhost:5173`. Vite hace proxy de `/api`, `/static` e `/imprimir`
al backend, así que no hay problemas de CORS.

## Estructura del Proyecto

```
Sunalyze/
├── app/                  # Backend Flask (API JSON + plantillas PDF)
│   ├── controllers/      # Lógica de negocio
│   ├── models/           # Modelos de base de datos (incl. project.py)
│   ├── routes/           # Blueprints y endpoints (incl. projects.py + SPA)
│   ├── services/         # Servicios auxiliares
│   ├── utils/            # Utilidades
│   ├── static/           # Assets de las plantillas PDF
│   └── templates/        # Plantillas Jinja2 (memoria/diagrama PDF)
├── frontend/             # SPA de React (rediseño Microsoft 365 / Fluent)
│   ├── src/
│   │   ├── components/   # Sistema de diseño (.sun-*) + shell
│   │   ├── screens/      # Dashboard, ProjectList, Wizard, Equipos, Memoria
│   │   ├── styles/       # Tokens + componentes + kit (CSS)
│   │   ├── lib/          # Formato es-ES, toasts, exportación, estados
│   │   └── api.js        # Cliente de la API Flask
│   └── dist/             # Build (gitignored; lo sirve Flask, se compila aparte)
├── config.py             # Configuración de la aplicación
├── run.py                # Punto de entrada
└── init_db.py            # Inicialización de la base de datos
```

El backend Flask actúa como **API headless** (JSON) y sirve la SPA de React
compilada. El frontend es una aplicación React + React Router con un sistema de
diseño Fluent/Office (verde Office, neutros Fluent, tipografía Segoe UI, cifras
tabulares).

## API Endpoints

### Análisis
- `POST /api/panel-analysis` - Calcular requerimientos de paneles
- `POST /api/diagrama-completo` - Generar diagrama funcional

### CRUD de equipos
- `GET/POST /api/panels` · `PUT/DELETE /api/panels/<id>` - Paneles
- `GET/POST /api/inverters` · `PUT/DELETE /api/inverters/<id>` - Inversores
- `GET/POST /api/wires` · `PUT/DELETE /api/wires/<id>` - Cables

### Proyectos
- `GET /api/projects` - Listar (filtro opcional `?estado=`)
- `POST /api/projects` - Crear
- `GET/PUT/DELETE /api/projects/<id>` - Obtener/actualizar/eliminar
- `POST /api/projects/<id>/duplicate` - Duplicar

### Memoria / diagrama
- `POST /imprimir/memoria-pdf` - Generar memoria técnica en PDF (WeasyPrint)
- `GET /api/circuit/<tipo>` - Esquema unifilar (SVG)

## Licencia

MIT
