# Accesibilidad — Fase 1: Fundamentos + lint

Investigación de criterios WCAG 2.1 (niveles A y AA) relevantes para esta fase y los
patrones concretos que se aplican en el frontend React + Vite de Sunalyze. El alcance de
esta fase es: semántica, skip-link, gestión de foco en navegación SPA, formularios,
utilidad `sr-only` y lint con `eslint-plugin-jsx-a11y`.

## Criterios WCAG 2.1 relevantes a esta fase

### 1.3.1 Info and Relationships (A)
La estructura y las relaciones transmitidas visualmente deben estar disponibles por
software (roles, semántica). Implica usar landmarks (`header`, `nav`, `main`, `footer`),
encabezados reales y asociar `label` con su control mediante `htmlFor`/`id`.

### 2.1.1 Keyboard (A)
Toda la funcionalidad debe operarse con teclado. Un `div`/`span` con `onClick` no es
enfocable ni activable con Enter/Espacio; debe ser un `<button>` (foco y activación por
teclado nativos).

### 2.4.1 Bypass Blocks (A)
Mecanismo para saltar bloques repetidos. Se cubre con un skip-link ("Saltar al contenido")
que es el primer elemento enfocable y apunta a `<main>`.

### 2.4.2 Page Titled (A)
La página tiene título. El `<title>` ya existe en `index.html`. Cada vista de la SPA
aporta un `<h1>` propio mediante `Topbar`.

### 2.4.3 Focus Order (A)
El orden de foco preserva el significado. En una SPA el foco "se queda" tras navegar; al
cambiar de ruta hay que mover el foco al contenedor principal/encabezado.

### 2.4.6 Headings and Labels (AA)
Encabezados y etiquetas descriptivos. Un único `<h1>` por vista y jerarquía coherente.

### 2.4.7 Focus Visible (AA)
El foco del teclado es visible. El design system ya define `--shadow-focus`; el skip-link
y el `<main>` enfocable reutilizan ese token.

### 3.3.1 Error Identification (A)
Los errores se identifican y describen en texto. Los errores de campo se asocian al input
con `aria-describedby` y se marca `aria-invalid`.

### 3.3.2 Labels or Instructions (A)
Se proporcionan etiquetas o instrucciones cuando el contenido requiere entrada del usuario.
Cada input tiene un `<label htmlFor>` asociado.

### 4.1.2 Name, Role, Value (A)
Nombre, rol y valor disponibles para tecnologías de asistencia. Los botones-icono sin texto
visible necesitan `aria-label`; los controles compuestos exponen estado.

### 4.1.3 Status Messages (AA)
Los mensajes de estado se anuncian sin recibir foco. La navegación SPA se anuncia con una
región `aria-live="polite"` (route announcer).

## Patrones aplicados y mapeo a criterios

| Mejora | Patrón | Criterios WCAG |
| --- | --- | --- |
| A1 Semántica | `div/span onClick` → `<button>` con estilo equivalente; landmarks `header/nav/main/footer` en el shell; un único `<h1>` por vista vía `Topbar` | 1.3.1, 2.1.1, 2.4.6 |
| A2 Skip-link | Enlace "Saltar al contenido" como primer foco, apunta a `<main id="main" tabindex="-1">` | 2.4.1 |
| A3 Foco en navegación SPA | Al cambiar de ruta, mover foco a `<main>` y anunciar la ruta con `aria-live="polite"` (route announcer integrado en el shell de la app) | 2.4.3, 4.1.3 |
| A4 Formularios | `<label htmlFor>` asociado por `id`; errores con `aria-describedby` + `aria-invalid`; `fieldset/legend` donde haya grupos | 1.3.1, 3.3.1, 3.3.2 |
| A5 `sr-only` | Utilidad CSS visually-hidden reutilizable + `aria-label`/texto sr-only en botones-icono | 4.1.2 |
| D1 Lint | `eslint` + `eslint-plugin-jsx-a11y` (flat config), script `lint`, corrección de violaciones en alcance | refuerza todos |

## Patrón visually-hidden (sr-only)

Técnica estándar accesible (no usa `display:none` ni `visibility:hidden`, que ocultan
también a lectores de pantalla):

```css
.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

El skip-link usa `.sr-only` por defecto y se vuelve visible al recibir foco
(`.sr-only:focus` / clase `skip-link`).

## Route announcer (SPA)

React Router no recarga la página, así que el lector de pantalla no anuncia el cambio de
vista ni se reposiciona el foco. Patrón:

1. Una región `aria-live="polite"` montada en el shell, fuera del flujo visible
   (`.sr-only`), cuyo texto se actualiza con el nombre de la vista en cada cambio de ruta.
2. Tras navegar, mover el foco programáticamente a `<main id="main" tabindex="-1">` con
   `focus({ preventScroll: true })`.

Esto satisface 2.4.3 (orden de foco) y 4.1.3 (status messages). Se integra en `AppLayout`
(shell de `/app`) reaccionando a `useLocation()`.

## Fuera de alcance (fases 2 y 3)

- Fase 2: refactor de accesibilidad en componentes del design system más allá de los
  formularios (menús, drawers/diálogos con `role="dialog"` + trampa de foco, tablas).
- Fase 2: contraste de color (1.4.3) y revisión de tokens.
- Fase 3: tests automáticos con axe-core / jest-axe y CI.
