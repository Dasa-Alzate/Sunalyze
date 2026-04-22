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

4. Compilar los assets (CSS):
```bash
npm install
npm run build
```
Esto ejecuta Tailwind/DaisyUI y genera `app/static/css/output.css`. Vuelve a ejecutarlo cada vez que cambies las clases o `app/static/css/input.css`.

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

## Ejecución

```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
Sunalyze/
├── app/
│   ├── controllers/      # Lógica de negocio
│   ├── models/           # Modelos de base de datos
│   ├── routes/           # Blueprints y endpoints
│   ├── services/         # Servicios auxiliares
│   ├── utils/            # Utilidades
│   ├── static/           # Archivos estáticos (CSS, JS)
│   └── templates/        # Plantillas Jinja2
├── config.py             # Configuración de la aplicación
├── run.py                # Punto de entrada
└── init_db.py            # Inicialización de la base de datos
```

## API Endpoints

### Análisis
- `POST /api/panel-analysis` - Calcular requerimientos de paneles
- `POST /api/diagrama-completo` - Generar diagrama funcional

### CRUD
- `GET/POST /api/panels` - Listar/crear paneles
- `GET/POST /api/inverters` - Listar/crear inversores
- `GET/POST /api/wires` - Listar/crear cables

## Licencia

MIT
