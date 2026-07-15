# Dark mode — investigación y decisiones

## Estado de partida

- `styles/tokens.css` tiene arquitectura de dos capas: paleta cruda (`--green-*`, `--ink-*`, `--amber-*`, `--blue-*`, `--red-*`) y capa semántica (`--bg-app`, `--surface-*`, `--text-*`, `--border-*`, `--primary`, estados). Los 110 componentes consumen solo la capa semántica; auditoría de colores hardcodeados en JSX: 0 reales (los hits son anchors `#features`, decoración del mock de ventana en `HeroPreview` y el default del picker de branding).
- `:root` declara `color-scheme: light` explícito.
- Ya existen medias queries de accesibilidad (`prefers-reduced-motion`, `prefers-contrast: more`) como precedente del patrón de overrides.

## Mecanismo elegido

- **Atributo `data-theme` en `<html>`** con overrides de la capa semántica bajo `[data-theme="dark"]`. Es el patrón estándar (compatible con SSR, sin FOUC si se estampa antes del primer paint) y el que usan los design systems de referencia (Radix, Fluent, GitHub Primer).
- **Preferencia del sistema como default**: sin elección guardada, se respeta `prefers-color-scheme: dark`. La elección explícita del usuario se persiste en `localStorage` (clave `sunalyze.theme`) y gana sobre el sistema.
- **Anti-FOUC**: script inline síncrono en `<head>` de `index.html` que estampa `data-theme` antes de cargar el bundle. Sin él, el usuario dark ve un flash blanco en cada carga.
- **Toggle binario** (light ⇄ dark) en el pie del sidebar, junto al `LanguageSwitcher`, siguiendo su mismo patrón (componente en `shared/`, i18n en namespace `settings`).

## Decisiones de paleta oscura

- Se redefine **solo la capa semántica**; la paleta cruda no cambia. Superficies basadas en grises cálidos coherentes con el `--cream` claro (no negro puro: #000 produce halos y peor legibilidad, referencia Material/Fluent dark).
- Jerarquía de superficies invertida por elevación: en dark, más elevado = más claro (`sunken < app < card < raised`).
- Textos: se reutiliza la escala `--ink-*` invertida donde alcanza el contraste AA (≥ 4.5:1 texto normal); acentos (`--primary`, links, estados) se aclaran un paso (500→400) porque los tonos 500-600 sobre fondo oscuro no llegan a AA.
- Sombras: en dark se sube la opacidad (las sombras negras sobre fondo oscuro desaparecen); se mantiene la misma escala de tokens.
- `color-scheme: dark` en el bloque para que formularios nativos, scrollbars y UA styles acompañen.

## Alcance

Solo frontend SPA. Quedan fuera: portal superadmin (Jinja), PDFs (WeasyPrint, siempre light por ser documentos imprimibles) y persistencia del tema en el perfil del usuario (posible iteración futura siguiendo el patrón de `locale`).
