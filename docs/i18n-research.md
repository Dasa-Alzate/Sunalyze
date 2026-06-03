# i18n — investigacion (Fase backend)

Soporte de varios idiomas en Sunalyze. Esta fase entrega solo el **backend que
habilita** la i18n del frontend: persistencia y deteccion de locale, codigos de
error estables en la API y emails locale-aware. La externalizacion de strings de
React (react-i18next, `format.js`) es una segunda fase de frontend.

## Decisiones de dominio

### UI != documento != dominio
- La **chrome de la UI** se traduce (Fase 2 frontend).
- La **memoria tecnica PDF** se mantiene **siempre en espanol**: es un artefacto
  legal del mercado espanol (ITC-BT-40), su idioma es del dominio, no de la UI.
  No se localiza.
- Hay **terminos de dominio que NO se traducen** (glosario do-not-translate).

### Glosario do-not-translate
Terminos tecnicos/normativos que se conservan literalmente en cualquier idioma de
la UI. No deben pasar por `t()` ni traducirse en catalogos:

| Termino | Que es |
|---------|--------|
| CUPS | Codigo Unificado de Punto de Suministro (identificador de suministro electrico) |
| kWp | Kilovatio pico (potencia pico del campo FV) |
| kWh / MWh | Energia |
| Wp | Vatio pico (por panel) |
| Voc | Tension de circuito abierto |
| Isc | Corriente de cortocircuito |
| Vmp / Imp | Tension / corriente en el punto de maxima potencia |
| MPPT | Maximum Power Point Tracking (seguidor del inversor) |
| ITC-BT-40 | Instruccion tecnica complementaria del REBT (instalaciones generadoras) |
| REBT | Reglamento Electrotecnico de Baja Tension |
| RD 1699/2011 | Real decreto de conexion a red de pequena potencia |
| PVGIS | Photovoltaic Geographical Information System (fuente de irradiacion) |
| string | Serie de paneles (no traducir como "cadena") |
| inverter / inversor | Se acepta el termino tecnico; producto de catalogo |
| tilt / azimuth | Inclinacion / orientacion (mantener en datasheets) |
| STC / NOCT | Condiciones de ensayo de modulos |

Regla practica: unidades fisicas (SI y derivadas), siglas normativas, codigos de
norma y nombres propios de sistemas/fuentes **nunca** se traducen.

## Backend: estrategia (sin librerias de i18n)

Se prefiere stdlib + lo que Flask ya ofrece (`request.accept_languages`). No se
introduce Babel ni catalogos gettext en el backend; la traduccion de la UI vive
en el cliente.

### Persistencia del locale
- `User.locale` (`String(5)`, default `'es'`, `server_default='es'`). Formato
  corto tipo `es`, `en`, `es-ES`. Se expone en `to_dict()` y en el payload de
  sesion.

### Deteccion / resolucion del locale activo
Precedencia (helper `app.i18n.resolve_locale`):
1. `user.locale` si hay usuario autenticado y tiene locale.
2. Cabecera `Accept-Language` negociada contra los locales soportados
   (`request.accept_languages.best_match`).
3. Default `es`.

Se normaliza a la parte de idioma (`es-ES` -> `es`) contra `SUPPORTED_LOCALES`.

### Codigos de error en la API
La API devuelve **mensajes en espanol** hoy. Para que el frontend pueda traducir
por codigo sin convertir el backend en sistema de traduccion, cada `DomainError`
lleva un `code` estable (string namespaced, p. ej. `auth.invalid_credentials`,
`project.not_found`). El body de error pasa de `{error, details?}` a
`{error, code, details?}`. Se mantiene `error` (compat); se anade `code`.

Esquema de codigos (namespace.snake_case):
- Generales por clase: `error.bad_request`, `error.validation`, `error.not_found`,
  `error.unauthorized`, `error.forbidden`, `error.conflict`, `error.internal`.
- Especificos de dominio asignados en el `raise` (segundo argumento `code=`),
  p. ej. `auth.invalid_credentials`, `auth.account_locked`, `auth.email_taken`,
  `project.not_found`, `invitation.not_found`, etc.
- Si un `raise` no especifica `code`, se usa el de la clase (degradado seguro).

### Emails locale-aware
`EmailService.render/send` aceptan `locale`. La plantilla se resuelve por
locale: `emails/<locale>/<archivo>` con fallback a `emails/<archivo>` (base `es`
actual). El asunto se toma de un catalogo por locale con fallback a `es`. Las
rutas pasan `user.locale` del destinatario. Hoy solo existe `es` (base); queda el
hueco para `en` sin traducir todo aun.

## Para la Fase 2 (frontend)
- `GET /api/auth/me` expone `locale` en el payload -> el provider de i18n lo usa.
- Catalogo de **codigos de error** a mapear a mensajes traducidos en el cliente
  (la API ya manda `code` + `message`).
- `format.js` debe dejar de fijar `es-ES` y seguir el locale activo.
- Switcher de idioma -> PATCH de `user.locale` (endpoint a definir en Fase 2).
