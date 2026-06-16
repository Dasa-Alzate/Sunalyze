# Generation input validation — research and plan

## Objetivo
Rechazar entradas basura en la generacion de diagramas (circuit) y de la memoria PDF
con HTTP 422 (tipo/rango/presencia), reutilizando el mecanismo pydantic v2 +
`register_error_handlers` ya existente.

## Mecanismo de 422 reutilizado
`app/errors.py` registra `@app.errorhandler(PydanticValidationError)` que convierte
cualquier `pydantic.ValidationError` (la que lanza `Schema(**data)`) en:
`{"error": "Datos invalidos", "code": "error.validation", "details": [{"field","msg"}]}` con 422.
Tambien existe `app.errors.ValidationError` (DomainError, status 422) que ya usan los
services para presencia. Patron a copiar: `app/schemas/templates.py` + `app/routes/templates.py`
(`data = Schema(**body)` en la ruta, antes de tocar el service).

## Circuit
- Ruta real: `app/routes/circuit.py` -> `CircuitDiagramService.generate(diagram_type, request.args.to_dict())`.
- `CircuitDiagramService` (app/services/circuit_diagram_service.py) valida `has_template`
  y presencia de 8 `REQUIRED_FIELDS` (panel_model, panel_voc, panel_isc,
  panels_per_string, num_strings, dc_fuse_i, dc_switch_v, dc_cable_section).
- `CircuitService.config_from_dict` (app/services/circuit/service.py) coacciona con
  `_float`/`_int` que tragan basura (default si falla). Nombres EXACTOS de params leidos:
  panel_model, panel_voc, panel_isc, panels_per_string, num_strings, dc_fuse_i,
  dc_switch_v, dc_cable_section, inverter_model, inverter_power, inverter_output_i,
  ac_phases, ac_mcb_i, ac_rcd_i, ac_rcd_sensitivity, ac_cable_section,
  has_fuses/has_battery (bool flags), battery_model, ac_has_zero_injection,
  ac_zero_injection_model.
- AMBIGUEDAD: la consigna pide "plantillas nombradas sin params siguen 200". Hoy NO es
  cierto: sin params devuelven 422 por presencia (verificado: GET /api/circuit/solar-basico
  -> 422). Resolucion: NO romper el comportamiento actual (no-regresion manda). La nueva
  validacion solo se aplica a los campos que SI se envian (si se envia, debe ser valido;
  si no se envia, se mantiene el chequeo de presencia tal cual hoy). Asi se respeta la
  regla (b) "el chequeo de presencia se mantiene" sin contradiccion.

### Schema circuit (todos los campos opcionales -> solo validan si se envian)
panel_voc float gt=0 le=2000; panel_isc float gt=0 le=500;
panels_per_string int ge=1 le=100; num_strings int ge=1 le=100;
dc_fuse_i float gt=0 le=500; dc_switch_v float gt=0 le=2000;
inverter_power float gt=0 le=10000; inverter_output_i float gt=0 le=2000;
ac_phases int in {1,3}; ac_mcb_i float gt=0 le=2000; ac_rcd_i float gt=0 le=2000;
panel_model/dc_cable_section/inverter_model/ac_cable_section str min_length=1 max_length=120.
Validar en el route, sobre request.args, ANTES de delegar al service.

## Memoria
- Ruta: `app/routes/main.py` -> `generar_memoria_pdf` -> `MemoriaService.generar_pdf(request.form)`.
- `MemoriaService.REQUIRED_FIELDS` (23 campos) + `_build_template_vars` enumera ~70 keys.
- Campos del formulario reales (de `_build_template_vars` + ids + battery):
  ids: panel_id, inverter_id, battery_id (int>0, opcionales salvo logica del service).
  numericos electricos: hired_power_kw(gt0), input_v, panels_peak_power_kw, panels_number(ge1),
  mppt_inputs(ge1), wire_dc_length, wire_dc_section?, wire_ac_length, wire_ground_length,
  protections_dc_thermal_v_max, protections_dc_breaker_i, protections_ac_thermal_i,
  protections_ac_diff_i, panel_temp_min_limit, panel_temp_max_limit, panels_surface,
  panels_inclination, panels_azimut, altitude, annual_production, annual_irradiance,
  panels_output_i_max_expected, panels_output_i_max_oversized, inverter_output_i_max_expected,
  battery_quantity(ge1). geo: latitude(-90..90), longitude(-180..180).
  textos: location, client_name, address, zipcode, catastral_reference,
  energy_company_name, energy_company_cups, input_v_type, inyection_type, panels_place,
  panels_disposition, inverter_place, inverter_phases, protections_ac_transitory_surge_model,
  *_verbosed, date, etc (opcionales, max_length razonable).
- Validar en `generar_memoria_pdf` sobre request.form ANTES de construir el PDF.
- CRITICO no-regresion: para inputs validos, los 3 SVGs deben quedar identicos. Baseline md5:
  svg_cc 5901 5d5dccd96edf230fda929f9add957f4e
  svg_ca 10123 475a5f0a384edfddf35ba4f83191acab
  svg_sistema 14481 0f8820758d8af22cb6d789d68cda97b2
  (los numeros 10123/6637/15196 del prompt no existen en el repo; el unico que coincide es
  svg_ca=10123). MANTENER el try/except degrade de _build_circuit_svgs intacto.
- El schema NO debe convertir strings de form en otra cosa: form manda strings; pydantic
  v2 coacciona str->float/int igual que hoy hace el service, asi que las vars de plantilla
  siguen recibiendo lo mismo (el service ya re-lee de form_data crudo, no del schema).

## Frontend
- circuit: `frontend/src/services/diagram-renderer/index.jsx` `CircuitSvg` muestra fallback
  generico al fallar. Mejora minima: leer el cuerpo de error 422 y mostrar el mensaje del
  backend en lugar del fallback mudo. `CircuitDiagram.jsx` usa preview.error como fallback.
- memoria: `MemoriaPreview.jsx` hace form POST con target=_blank; el 422 ya abriria JSON en
  pestana. Ya hay guard cliente de required. Mejora minima sin reescribir: dejar el guard;
  el backend 422 es la red de seguridad. No se intercepta facil un POST target=_blank.

## Reglas
SIN comentarios inline. Tests en sqlite aislado. Commits en espanol. No push.
Dos commits: (1) circuit, (2) memoria + frontend.
