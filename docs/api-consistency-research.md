# API consistency: research and analysis

## Objetivo
Hacer que la superficie de endpoints sea entendible de una sola pasada mediante (a)
normalizacion de inconsistencias de verbo/nombre y (b) un mapa de API autogenerado.

## Convencion REST adoptada
- Recursos = sustantivo plural ingles (kebab-case si multipalabra).
- Coleccion: `GET/POST /api/<recurso>`. Item: `GET/PATCH/DELETE /api/<recurso>/<id>`.
- Acciones no-CRUD: `POST /api/<recurso>/<id>/<verbo>` (verbo kebab-case).
- Sub-recursos anidados: `/api/<recurso>/<id>/<subrecurso>`.

## Estado actual (hallazgos)
- El frontend React centraliza llamadas en `frontend/src/api/client.js` (helpers
  `get/post/put/patch/del`). No hay callers crudos de React fuera de ese fichero.
- Update de item usa `PUT` en `crud.py` (panels/inverters/batteries/wires) y en
  `projects.py` (projects). `members` y `templates` ya usan `PATCH`.
  `PUT /api/templates/<id>/content` usa `PUT`.
- Outliers en espanol en el blueprint `main`: `POST /api/panel-analysis` y
  `POST /api/diagrama-completo`.

### Callers de los outliers
- `panel-analysis`: usado por React via `api.analyze` (`client.js`) y tambien por el
  frontend legacy `app/static/js/app.js` (fetch crudo, x2).
- `diagrama-completo`: NO lo usa React. Solo lo usa el frontend legacy
  `app/static/js/app.js` (fetch crudo), servido por `app/templates/index.html`.

## Decisiones

### 1. Verbo de update unificado a PATCH (se aplica)
Cambiar a `PATCH` el update de item en `crud.py` y `projects.py`, y
`PUT /api/templates/<id>/content` -> `PATCH`. En `client.js`, cambiar las llamadas
`put(...)` correspondientes a `patch(...)`. Se retira `PUT` (sin alias): el verbo viejo
debe responder 405.

### 2. Outliers en espanol: EXCEPCION CONOCIDA (no se renombra)
`panel-analysis` y `diagrama-completo` tienen callers crudos en el frontend legacy
(`app/static/js/app.js`, servido por `app/templates/index.html`) que NO estan centralizados
en `client.js`. Renombrarlos exigiria propagar cambios al JS legacy fuera del perimetro
seguro y arriesgaria romper esa UI. Siguiendo la regla "prioriza no romper el frontend por
encima de la pureza", se dejan como estan y se anotan como excepcion conocida en
`docs/api-conventions.md`.

## Generador `flask api-map`
Comando CLI que introspecta `app.url_map`, filtra rutas `/api`, agrupa por blueprint, y
escribe `docs/api-map.md`: tabla por blueprint con metodo(s) + ruta + endpoint + primera
linea del docstring de la vista. Ordenado, legible, idempotente.
