# Convenciones de API

Estas reglas hacen que la superficie de endpoints sea entendible de una sola pasada. El
mapa autogenerado vive en [`api-map.md`](api-map.md) (regenerable con `flask api-map`).

## Reglas

- **Recursos**: sustantivo plural en ingles. Kebab-case si es multipalabra.
- **Coleccion**: `GET /api/<recurso>` (listar), `POST /api/<recurso>` (crear).
- **Item**: `GET /api/<recurso>/<id>` (leer), `PATCH /api/<recurso>/<id>` (actualizar
  parcial), `DELETE /api/<recurso>/<id>` (borrar).
- **Acciones no-CRUD**: `POST /api/<recurso>/<id>/<verbo>`, verbo en kebab-case
  (p. ej. `/api/projects/<id>/duplicate`, `/api/catalogs/<id>/subscribe`).
- **Sub-recursos anidados**: `/api/<recurso>/<id>/<subrecurso>`
  (p. ej. `/api/projects/<id>/documents`).

## Verbo de actualizacion: PATCH

El update de item usa **`PATCH`** de forma uniforme en toda la API (los cuerpos son
parciales). Se retiro `PUT` como verbo de actualizacion: una peticion `PUT` al recurso
responde `405 Method Not Allowed`.

Endpoints afectados por la normalizacion a PATCH:

- `PATCH /api/{panels,inverters,batteries,wires}/<id>` (antes `PUT`).
- `PATCH /api/projects/<id>` (antes `PUT`).
- `PATCH /api/templates/<id>/content` (antes `PUT`).

`members` y `templates` ya usaban `PATCH`.

El frontend de React centraliza todas las llamadas en `frontend/src/api/client.js`; los
helpers de actualizacion usan `patch(...)` en lockstep con el backend.

## Excepciones conocidas

Estos endpoints no siguen el naming en ingles de la convencion. Tienen callers crudos
(fetch directo) en el frontend legacy `app/static/js/app.js`, servido por
`app/templates/index.html`, fuera del cliente centralizado de React. Renombrarlos exigiria
propagar cambios a ese JS legacy y arriesgaria romper esa UI; priorizando no romper el
frontend por encima de la pureza, se dejan como estan:

- `POST /api/panel-analysis` — analisis de dimensionamiento. Tambien lo consume React via
  `api.analyze` en `client.js`.
- `POST /api/diagrama-completo` — render del diagrama funcional. Solo lo consume el frontend
  legacy.
