# Onboarding con empty-states guiados — investigación

## Problema
Un usuario nuevo aterriza en `/app` (Dashboard) con 0 proyectos: ve cuatro KPIs a cero,
una tabla de «Proyectos recientes» con un mensaje de una línea y paneles laterales.
No hay guía del flujo del producto ni un CTA dominante.

## Estado actual del código

### Dashboard (`frontend/src/features/dashboard/Dashboard.jsx`)
- Carga `api.projects.list()`; estados: `error` → `ErrorState`, `null` → `Spinner`, lista → KPIs + grid.
- Con `projects.length === 0` hoy renderiza igualmente los KPIs a cero y la tabla vacía
  con el texto «Aún no hay proyectos. Crea el primero con “Nuevo diseño”.»
- La acción de crear proyecto en toda la app es `nav('/app/diseno')` (Topbar «Nuevo diseño»,
  tarjeta «Empezar»).

### ProjectList (`frontend/src/features/projects/ProjectList.jsx`)
- Ya tiene empty-state con las clases `sun-empty` (icono, título, descripción, acciones)
  y CTA «Crear proyecto» → `nav('/app/diseno')`. Distingue 0 proyectos vs. filtro sin resultados.

### Patrones de UI reutilizables
- `frontend/src/shared/ui/index.jsx`: `Topbar`, `Card`, `Btn`, `Icon` (lucide por nombre kebab).
- `frontend/src/styles/components.css`: `.sun-empty`, `.sun-empty__icon`, `.sun-empty__title`,
  `.sun-empty__desc`, `.sun-empty__actions`.
- Textos de features en español hardcodeado (Dashboard y ProjectList no usan `useTranslation`);
  el i18n existente (`services/i18n`) solo cubre otros namespaces. Se mantiene el patrón.

### Patrones de test (`frontend/src/test/*.test.jsx`)
- `vi.mock('@/api/client', …)` con `api` de `vi.fn()`; `MemoryRouter` (+ `Routes` con ruta
  sonda para asertar navegación, como en `batteries.test.jsx`); mock de `@/services/auth`
  (`useAuth: () => ({ can: () => true })`) y `@/services/toast`.
- `PendingWorkPanel` usa `api.pendingWork` y `useTransition`; en tests de Dashboard se mockea
  el módulo a `null`.

## Flujo del producto (para los pasos del onboarding)
1. Crear proyecto (ubicación y consumo) → `/app/diseno`.
2. Elegir equipos (paneles, inversor, baterías).
3. Revisar el análisis (producción y finanzas).
4. Generar la memoria técnica firmable.

## Decisiones
- Dashboard: con 0 proyectos se sustituye KPIs + grid por una única tarjeta de bienvenida
  (`Card` + clases `sun-empty` + lista visual de 4 pasos) con CTA primario
  «Crear tu primer proyecto» → `nav('/app/diseno')`. Con ≥1 proyecto, cero cambios.
- ProjectList: ya cumple «mensaje + CTA»; solo se alinea el texto del CTA a
  «Crear tu primer proyecto» cuando no existe ningún proyecto.
- Sin librerías nuevas, sin i18n nuevo, sin tours ni wizards. Alcance: dashboard + proyectos.
