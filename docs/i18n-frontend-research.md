# i18n frontend — investigacion y plan

## Estado de partida (verificado en codigo)

- Backend ya integrado en `main`:
  - `User.locale` (`String(5)`, default `es`, server_default `es`) — `app/models/user.py`.
  - `/api/auth/me` devuelve `{ user{...locale}, role, permissions, flags, locale }` — `app/routes/auth.py:_session_payload`.
  - `app/i18n.py`: `resolve_locale(user)` por precedencia user > Accept-Language > `es`;
    `SUPPORTED_LOCALES = ('es', 'en')`, `DEFAULT_LOCALE = 'es'`, `normalize_locale()`.
  - Errores de dominio: `{error: message, code}` con codigos estables (`auth.invalid_credentials`,
    `invitation.expired`, `project.not_found`, ...) — `app/errors.py` + `grep code=`.
- Frontend sin libreria i18n; strings en español inline.
  - `frontend/src/shared/format.js` fija `es-ES` en `num/int/dec/pct`.
  - `AuthProvider` consume `/me` via `api.auth.me()` y expone `refresh()`.
  - `api/client.js` ya tiene helper `patch()` y `ApiError(message, status, data)` (data lleva `code`).

## Decisiones

### Libreria
`i18next` + `react-i18next` (estandar de facto; interpolacion, plurales ICU, namespaces,
lazy-load futuro). Sin backend de carga: recursos importados estaticamente (es/en).

### Format: UI vs tecnico (decision abierta #2 de pending-work §3)
Se separan dos convenciones:
- **Numero de UI** (`num/int/dec/pct`): locale-aware. Sigue el idioma activo de la UI
  (es -> coma decimal, en -> punto). Para contadores, badges, totales de interfaz.
- **Numero tecnico de dominio** (`techNum`/`techDec`): SIEMPRE convencion `es-ES`
  (coma decimal) con independencia del idioma de la UI. Las cifras de ingenieria
  (Voc, kWp, secciones, caidas de tension) y la memoria PDF son artefactos del
  *dominio* español (ITC-BT-40); cambiarlas a punto decimal romperia coherencia con
  la memoria legal. Por eso el dominio mantiene su locale fijo.
- `date` tambien locale-aware (UI).

Implementacion: `format.js` lee el locale activo de un singleton que el provider i18n
mantiene sincronizado (`setActiveLocale`), evitando acoplar `format.js` a React.

### Slice externalizado (primer corte, NO 100%)
Namespaces en `locales/<lang>/`:
- `nav.json` — navegacion del `AppLayout` (Resumen, Proyectos, ...), brand-side labels.
- `auth.json` — pantallas `features/auth/Auth.jsx` (login, signup, forgot, reset, verify).
- `common.json` — primitivas `shared/ui` (botones, estados, validaciones, spinner,
  export, error) y acciones comunes.
- `errors.json` — mapa `code -> mensaje` para `ApiError`.
- `settings.json` — switcher de idioma y etiquetas de ajuste.

`en` arranca como copia traducible de `es` (mismas claves); se completa incrementalmente.

### Glosario do-not-translate
CUPS, kWp, kW, Wp, Voc, Isc, Vmp, Imp, MPPT, ITC-BT-40, RBT, AC, DC, string(s),
inverter (cuando es termino tecnico), CSV, PDF, XLSX. Estos NO van a los catalogos como
texto traducible; quedan literales o interpolados como variables.

### Switcher + persistencia
- Selector es/en accesible en el chip de usuario del sidebar (`AppLayout`).
- Persistencia: nuevo endpoint **`PATCH /api/auth/me`** `{locale}` que valida contra
  `SUPPORTED_LOCALES` (`normalize_locale`), actualiza `user.locale`, commitea y devuelve
  el `_session_payload`. PATCH por convencion REST (actualizacion parcial del recurso me).
- `api.auth.updateLocale(locale)` -> PATCH; el provider aplica el nuevo locale a i18next y
  refresca la sesion.

### Mapa de codigos de error
Util `messageForError(err, t)`: si `err.data.code` existe y hay traduccion en
`errors.<code>`, la usa; si no, cae al `err.message` del backend; ultimo recurso, generico.

## Verificacion
- Frontend: `npm install && npm run build && npx eslint src && npm test` (0 warnings, tests verdes).
- Backend: `py_compile` de todo `app/` + test del PATCH locale (actualiza, valida soportado,
  rechaza invalido) y no-regresion de `tests/`.
