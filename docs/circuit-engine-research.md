# Circuit engine — research & analysis (Fase 1 backend)

## Estado actual (`app/services/circuit/`)
- `component.py` — base `Component` (ABC), `CELL=120`, `render(style, **kwargs)` devuelve SVG body sin `<g>`. Helpers `_path/_rect/_line/_circle/_text`.
- `diagram.py` — compositor grid. `place / place_scaled / wire / dot / box / label`. Render aplica `translate(gx*C, gy*C)`, `scale`, y `rotate(orientation, 60, 60)`.
- `wire.py`, `box_area.py` — dataclasses simples.
- `config.py` — `DiagramStyle`, `DCConfig`, `ACConfig` (ya tiene `has_battery`/`has_zero_injection`), `SystemConfig`.
- `circuit_service.py` — `CircuitService` (facade dominio): `generate_cc_vertical / generate_grid_connection / generate_full_system`, `config_from_dict`.
- `components/` — 13 clases (Fuse, Switch, Inverter, CircuitBreaker, Differential, SurgeArrester, Ground, StringGroup, Meter, GridSymbol, FVGenerator, ZeroInjection, Battery).
- `diagrams/` — 3 building blocks: DCStringsDiagram, GridConnectionDiagram, FullSystemDiagram.

## Consumidores
- `app/services/memoria_service.py::_build_circuit_svgs` → importa `CircuitService, DCConfig, ACConfig, SystemConfig` desde `app.services.circuit`; produce `svg_cc / svg_ca / svg_sistema`.
- `app/services/circuit_diagram_service.py::CircuitDiagramService` → importa `CircuitService`; `GENERATORS={'cc-strings': generate_cc_vertical}`; valida campos.
- `app/routes/circuit.py` → `GET /api/circuit/<diagram_type>` sobre `CircuitDiagramService.generate`.
- Front `frontend/src/services/diagram-renderer/index.jsx::CircuitSvg` → `fetch('/api/circuit/cc-strings?...')`.

## Modelo de orientación (clave para connection points)
`Diagram.render` rota el grupo del componente con `rotate(orientation, 60, 60)` (centro de celda local). Para que un punto de conexión absoluto coincida con el wire, `connection_points(orientation)` debe aplicar la MISMA transformación a las coords locales: rotación CW de `theta` grados alrededor de `(60,60)`.

Rotación CW de un punto `(x,y)` alrededor de `(cx,cy)=(60,60)`:
- 0°:   `(x, y)`
- 90°:  `(cx - (y-cy), cy + (x-cx))`  → `(60-(y-60), 60+(x-60))`
- 180°: `(cx-(x-cx), cy-(y-cy))`      → `(120-x, 120-y)`
- 270°: `(cx + (y-cy), cy - (x-cx))`  → `(60+(y-60), 60-(x-60))`

Validación: Fuse `out=(60,120)`. orientation=90 → `(60-(120-60), 60+(60-60)) = (0,60)`. Coincide con el eje que en `dc_strings` queda izquierda→bottom tras rotar 90 (la entrada por izquierda). Correcto.

## Decisiones de arquitectura
1. Subcarpeta `core/` con: `diagram.py`, `component.py`, `wire.py`, `box_area.py`, `config.py`, `style.py` (re-export de DiagramStyle para cumplir el pedido sin romper imports), y `geometry.py` NUEVO (rotación de puntos).
2. `components/` y `diagrams/` se quedan; sus imports `..component`/`..config` pasan a `..core.component`/`..core.config`.
3. `circuit_service.py` → `service.py` (mismo `CircuitService`). `__init__.py` mantiene la fachada (re-exporta `CircuitService`, configs, `Diagram`, etc.) para NO romper `memoria_service` ni `circuit_diagram_service`.
4. `geometry.py`: `rotate_point(x,y,orientation)` + transform de puntos. `Component` gana `ports: dict[str,(x,y)]` (default vacío o derivado) y `connection_points(orientation)`.
5. `Diagram` gana: registro del placement al hacer `place`, `port(placement, name)` → coord grid absoluta, `connect(placA, nameA, placB, nameB)`.
6. `diagrams/registry.py`: `TEMPLATES = {name: builder(config)->svg}` con las 4 nombradas + las 3 building-block accesibles.
7. API: `routes/circuit.py` añade `GET /api/circuit/templates`; `CircuitDiagramService` enruta cualquier template y mantiene alias `cc-strings`.

## No-regresión
- Las 3 building blocks no cambian salida (no toco su cableado salvo opcional). `memoria_service` sigue llamando `generate_*`.
- `cc-strings` sigue 200 vía alias.

## Tests (unittest, BD sqlite aislada)
- geometry: `connection_points` 0/90/180/270 para Fuse e Inverter.
- `Diagram.connect` dibuja `<line>` entre puertos.
- 4 plantillas → SVG válido; `solar-sin-fusibles` sin fusible, `solar-con-fusibles` con; `solar-con-baterias` con batería.
- API `/templates` lista 4+; cada `<template>` 200 svg; alias 200.
- memoria `_build_circuit_svgs` devuelve 3 SVGs.
