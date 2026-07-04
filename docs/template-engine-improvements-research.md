# Template engine — research y plan de mejora

Módulo: `app/services/template_engine/` (parser propio anti-SSTI, sin `eval`), consumido por
`DocumentService` (PDF WeasyPrint) y `TemplateService` (CRUD + `validate_content` al guardar).

## Responsabilidades del módulo

- `tokenizer.py`: gramática restringida (números, strings, rutas `entidad.atributo`, `+ - * /`,
  paréntesis, coma, pipe). Rechaza dunders y guion bajo inicial en cada segmento del nombre.
- `parser.py`: parseo del interior de `{{ ... }}` a `ParsedExpression` (base + cadena de
  filtros); evaluación aritmética con shunting-yard propio; `round`/`sum`; `render_text`.
- `filters.py`: registry de filtros de formato locale-aware (`number`, `thousands`, `money`,
  `currency`, `date`, `ellipsis`, `upper`, `lower`).
- `context.py`: `build_context` (entidades None-safe) + `ContextResolver` (getattr solo sobre
  whitelist del catálogo).
- `catalog.py`: única fuente de la whitelist y del metadato de variables por `DocumentKind`.
- `jurisdiction.py`: perfil de presentación por país (locale/currency/page_size).
- `renderer.py`: secciones -> HTML escapado para WeasyPrint.

## Seguridad anti-SSTI (auditoría)

Probados payloads clásicos y exóticos (`__class__`, `__mro__`, `__subclasses__`,
`__globals__`, `getattr(...)`, `panel['x']`, `x if y else z`, `attr('__class__')`,
`system('ls')`, `9**9**9`, `'a'*99999999999`). **Todos bloqueados.** Defensa en capas:
tokenizer rechaza dunder/`_`, no hay indexado ni llamada a métodos, `getattr` solo sobre
whitelist, sin `eval/exec/compile`. **No se encontró bypass de ejecución de código.**

Sí hay agujeros de **robustez** (no de ejecución) que degradan a 500 o a salida fea:

1. `apply_filter` solo captura `TypeError`. Un argumento string no numérico
   (`{{ x | number('abc') }}`) lanza `ValueError` que escapa como **500**, incluso en modo
   render seguro (placeholder). Un typo del autor tumba la generación entera del PDF.
2. Literales string que Python parsea a no finito (`{{ '1e999' * 1 }}` -> `inf`) filtran
   `inf`/`nan` al documento.

## Bugs de comportamiento confirmados

3. **Filtros numéricos no None-safe**: `number`/`thousands`/`money`/`currency` lanzan
   `TemplateError` ante `None`, mientras `date`/`upper`/`lower`/`ellipsis` devuelven `''`. Doble
   impacto:
   - `validate_content` (modo `raise`) **rechaza plantillas legítimas**: guardar
     `{{ finance.net_capex | money }}` falla porque el contexto de validación tiene valores
     `None`.
   - En render real (placeholder) una entidad opcional ausente produce
     `[finance.net_capex | money]` visible en el PDF, contradiciendo el diseño ("las opcionales
     resuelven a vacío").

## Mensajes de error al autor

`render_text`/`_render_body` en modo `raise` re-lanzan el `TemplateError` pelado, sin decir en
qué `{{ ... }}` ocurrió. `validate_content` añade el índice de sección pero no la expresión
concreta. Falta contexto de expresión.

## Rendimiento

`parse_expression` (que tokeniza) se ejecuta por cada `{{ ... }}` en cada render; no hay
compilación/caché. Las expresiones son puras (sin datos de tenant) -> cacheables.

## Lista priorizada de mejoras (quirúrgicas)

1. (ALTA, robustez) `apply_filter` captura `ValueError` además de `TypeError`; rechazo de
   `inf`/`nan` en aritmética/coerción. Convierte 500 en placeholder/422 limpio.
2. (ALTA, correctitud) None-safety de `number`/`thousands`/`money`/`currency` (y `default`
   como par natural). Desbloquea `validate_content` y elimina placeholders feos en PDF.
3. (MEDIA, DX) Contexto de expresión en errores modo `raise` + `validate_content` con contexto
   completo. El autor sabe qué expresión y qué variable/filtro falló y dónde.
4. (MEDIA, filtros de uso común) Nuevos filtros `default`, `capitalize`, `title`.
5. (MEDIA, rendimiento) `lru_cache` en `parse_expression` (seguro: `ParsedExpression` no se
   muta, las excepciones no se cachean).

Fuera de alcance a propósito: cambios de esquema BD (innecesarios); reescritura del parser
(defensa sólida); filtro `percent` (semántica ambigua fracción vs. porcentaje -> footgun).

## No-regresión

Snapshot dorado de un render con valores válidos (no None) guardado; debe reproducirse
byte-a-byte tras los cambios. Los cambios solo tocan rutas None/error, no el camino feliz.
