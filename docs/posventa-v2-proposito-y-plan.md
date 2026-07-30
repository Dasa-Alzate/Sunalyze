# Posventa v2 — propósito, estado real y plan de viabilidad comercial

Revisión de **2026-07-29**. Sucede a `docs/posventa-research.md` (fase 1, backend)
y `docs/posventa-frontend-plan.md` (fase 2, frontend), que siguen siendo válidos
como descripción de lo construido. Este documento **redefine el propósito** del
módulo y deriva de ahí la lógica de negocio que le falta para ser vendible.

---

## 1. El propósito, replanteado

Lo construido está pensado como **seguimiento**: registrar visitas, incidencias y
lecturas de una instalación entregada. Esa definición no sostiene un módulo
comercial, porque el instalador ya tiene una hoja de cálculo que hace eso gratis.

La definición que propongo:

> **El módulo de posventa es el instrumento que convierte la obligación legal y
> contractual del instalador en un proceso gestionable y demostrable.** No es un
> tablero de tareas ni un monitor de producción: es la prueba de que la
> instalación que firmaste sigue cumpliendo, y el mecanismo para que cada
> incidencia acabe imputada a quien la debe pagar.

### Por qué encaja con nuestro moat y «monitorización» no

Sunalyze posee algo que ningún portal de fabricante ni Solarus tiene: **la
memoria técnica firmada por un técnico competente**, con el expediente de
legalización detrás. Ese documento genera responsabilidad que dura años y hoy se
firma y se olvida.

Competir en ingesta de datos de inversor es pelear en el terreno del rival sin su
hardware. Competir en *quién paga esta avería* es pelear en el nuestro, porque la
respuesta está en el expediente que ya tenemos: qué equipo se instaló, con qué
ficha técnica, quién lo firmó y cuándo se puso en marcha.

### Los relojes que nadie está contando

En una instalación coexisten **cinco garantías con contrapartes distintas**:

| Garantía | Plazo típico | Contraparte |
|---|---|---|
| Producto del módulo | 12–15 años | Fabricante |
| Rendimiento del módulo | 25–30 años (curva de degradación) | Fabricante |
| Inversor | 5–10 años, ampliable | Fabricante |
| Batería | 10 años **o** N ciclos, lo que llegue antes | Fabricante |
| Mano de obra y montaje | 2–5 años | Instalador |
| Conformidad legal | 3 años (bienes vendidos desde 1-1-2022) | Vendedor, por ley |

Hoy todo eso se resume en un único campo `Installation.warranty_until`. Es la
simplificación que más valor destruye del módulo.

---

## 2. Estado real del código (2026-07-29)

### Lo que existe y funciona

- `app/models/installation.py`: `Installation`, `MaintenanceVisit`, `Incident`,
  `ProductionReading`. Multi-tenant por `org_id`, `to_dict()` con fechas ISO.
- `app/services/installation_service.py`: `create_from_project` (exige proyecto
  `aprobado`, 1:1), `set_status`, CRUD anidado, `performance_summary`.
- `app/routes/posventa.py`: REST completo tras el flag `posventa` (default OFF).
- Frontend `features/posventa`: workspace, detalle con pestañas, paneles de
  mantenimiento, incidencias y rendimiento con gauge SVG.
- Estados de instalación sin transiciones estrictas — **decisión deliberada y
  correcta**: el estado operativo no es lineal (operativa ↔ incidencia,
  mantenimiento puntual, baja).
- Separación correcta entre `Incident` (operativo de la instalación) y
  `SupportTicket` (soporte de la plataforma).

### Los tres huecos estructurales

**1. No existe ningún dato de contacto en ningún modelo.** Verificado: ni
`telefono`, ni `movil`, ni `phone` aparecen en `app/models/*.py`.
`Project.cliente` es un `String(150)` con el nombre y nada más. El módulo no
puede avisar a nadie porque no sabe quién es.

**2. `Incident` es una lista de tareas con etiqueta de color.** Campos actuales:
`title`, `description`, `severity`, `status`, `opened_at`, `resolved_at`. No hay
categoría, ni imputación de coste, ni reloj, ni relación con la garantía.

**3. `Installation.warranty_until` es una sola fecha** para las seis garantías de
la tabla anterior.

Añadidos menores que también faltan: no hay modelo de contrato ni de SLA
(verificado, no existe nada en `app/models/`), y `MaintenanceVisit` se crea de una
en una a mano.

---

## 3. Contexto competitivo (de `analisis-competencia-v2.md`)

- **Portales de fabricante** (SolarEdge, FusionSolar, Sunny Portal, Victron VRM):
  gratis con el hardware. El instalador «vive con 4-5 portales abiertos».
- **Solarus** (España) es el competidor directo del módulo: monitorización
  multimarca, alertas por IA **y gestión de incidencias y mantenimientos**.
- Su ventaja declarada: **ingesta automática de datos de inversores**, que no
  tenemos. En la tabla de huecos esa ingesta está valorada **prioridad Media**,
  no Alta.
- Tesis estratégica del documento: no igualar a PVsyst en ingeniería ni a Aurora
  en diseño remoto, sino **profundizar el eslabón legal**, donde Wattwin y Ezzing
  son superficiales.

La conclusión operativa: el módulo no gana por datos, gana por **consecuencia
contractual del dato**.

---

## 4. La lógica de negocio que falta

Ordenada por valor comercial, no por facilidad de implementación.

### 4.1 Libro de garantías por equipo (no por instalación)

Al crear la instalación se generan filas de garantía derivadas del BOM del
proyecto. Cada fila: tipo, inicio, fin, **contraparte** (fabricante /
distribuidor / instalador / ley), documento que la respalda, y para baterías
también el límite en ciclos. Engancha directamente con las fichas técnicas
generadas y con la trazabilidad de procedencia del catálogo.

`Installation.warranty_until` pasa a ser derivado o se retira: no debe coexistir
con el libro dando una segunda verdad.

### 4.2 Imputación de coste en la incidencia

La pieza que convierte el registro en instrumento económico. Añadir a `Incident`:

- `category`: producción · avería de equipo · obra y estanqueidad ·
  comunicaciones · eléctrico y protecciones · uso del cliente · causa externa
- `attribution`: `garantia_fabricante` | `garantia_instalador` |
  `garantia_legal` | `fuera_de_garantia` | `causa_externa` |
  `pendiente_de_diagnostico`
- `warranty_id` (fila del libro que la cubre), `billable`, `cost_estimate`,
  `cost_actual`

Permite responder la única pregunta que importa: *¿esto lo pago yo o lo paga el
fabricante?* Y produce un número que cambia decisiones de compra: «este trimestre
he absorbido 4.200 € de averías que eran de fabricante».

### 4.3 SLA con reloj, y el estado que hoy falta

`response_due_at` y `resolution_due_at` calculados desde la severidad y la
política SLA de la organización (configurable, y por contrato si venden planes).
Marca de incumplimiento.

**El detalle que más importa: hace falta el estado `pendiente_de_tercero`**
(esperando RMA del fabricante). Ese estado **para el reloj de SLA**. Sin él, un
RMA de seis semanas parece negligencia propia en los indicadores del instalador,
y es justo donde su dinero está atrapado.

Ciclo de vida propuesto para `Incident`:
`abierta → diagnosticada → en_proceso → pendiente_de_tercero → resuelta → cerrada`
(cerrada = aceptada por el cliente). A diferencia del estado de la instalación,
aquí **sí** conviene transición controlada, porque alimenta relojes y coste.

### 4.4 Contacto en el proyecto y snapshot en la instalación

En `Project`: `contacto_nombre`, `contacto_email`, `contacto_movil`.

En `Installation`: **copia propia** de esos campos, porque el contacto de
posventa puede no ser el del proyecto — la vivienda cambia de manos, o quien paga
no es quien vive.

Y un registro de comunicaciones por incidencia (qué se comunicó, cuándo, por qué
canal, a quién). No necesita SMTP ni pasarela SMS: **registra que la comunicación
ocurrió**, que es lo que sirve como traza probatoria en una disputa.

### 4.5 Plan de mantenimiento generado, no tecleado

Una plantilla que al crear la instalación genere el calendario: revisión anual
visual y eléctrica, limpieza según zona de suciedad, firmware del inversor,
estado de salud de la batería, y la **inspección OCA periódica** donde el REBT la
exige. Con 200 instalaciones esto es la diferencia entre un módulo usable y uno
teórico.

### 4.6 Alerta de rendimiento honesta, sin API de inversor

No podemos ingerir del inversor, pero sí comparar la lectura mensual contra la
**expectativa mensual de PVGIS** —que ya consultamos— normalizada por periodo, y
abrir incidencia automática cuando la desviación supere un umbral durante N
periodos consecutivos.

Y que **la lectura la pueda enviar el propio cliente** mediante un formulario:
así la recogida de datos escala sin hardware.

> Límite honesto que no debe cruzarse en el discurso comercial: esto es un
> **chequeo documentado de ratio de rendimiento**, no monitorización en tiempo
> real. No debe venderse como lo segundo.

### 4.7 Contratos de mantenimiento — la viabilidad comercial

`MaintenanceContract` en la instalación: alcance, precio anual, periodicidad,
incluido/excluido, nivel de SLA, fecha de renovación.

De ahí salen tres cosas que se venden solas: **ingreso recurrente en riesgo** por
contratos que vencen, **pipeline de renovación**, y **rentabilidad por contrato**
(ingreso vs coste de incidencias imputadas). Convierte la posventa de un coste
que el instalador evita en un producto que vende — y es la razón por la que
pagaría por el módulo.

### 4.8 Acta de intervención firmable

Cada incidencia o visita resuelta emite un PDF con hallazgo, actuación, material
sustituido, horas y aceptación del cliente. Reutiliza WeasyPrint y el modelo de
firma de la memoria, ya existentes. Es el artefacto que protege al instalador.

---

## 5. Lo que NO construir

- **Ingesta de APIs de inversor** por ahora: el propio análisis competitivo la
  valora prioridad Media y es una noria de mantenimiento por fabricante.
- **Ticketing genérico**: para eso está `SupportTicket`; y Zendesk existe.
- **Optimizador de rutas de cuadrillas**: terreno ERP de OpusFlow, no nuestro.

---

## 6. Avisos de implementación

- **RGPD.** `Project.to_dict()` alimenta la exportación
  (`gdpr_service.py:52` serializa `p.to_dict()`), así que los campos de contacto
  entrarán en el export automáticamente. Hay que **verificar que la ruta de
  supresión también los alcanza**: son datos personales de una persona física
  distinta del usuario de la plataforma. La política de privacidad ya cubre
  «datos de proyecto», lo cual encaja sin cambios legales.
- **No duplicar la verdad de la garantía**: retirar o derivar
  `Installation.warranty_until` al introducir el libro.
- **Flag.** Todo lo nuevo sigue tras `posventa`; los contratos podrían merecer su
  propio flag si se venden como plan aparte.
- **Permisos.** Mantener el criterio de la fase 1 (reutilizar `PROJECT_VIEW` /
  `PROJECT_EDIT`) salvo para el coste imputado y los contratos, que son
  información económica y probablemente deban colgar de un permiso financiero.

---

## 7. Orden de ataque propuesto

1. **Contactos** (`Project` + snapshot en `Installation`) — desbloquea todo lo
   demás y es requisito de cualquier comunicación.
2. **Libro de garantías** derivado del BOM.
3. **Imputación de coste en la incidencia** + categorías.
4. **SLA con reloj** y el estado `pendiente_de_tercero`.
5. **Plan de mantenimiento generado.**
6. **Alerta de rendimiento** contra la expectativa mensual de PVGIS.
7. **Contratos de mantenimiento** (el de más superficie de UI, al final).
8. **Acta de intervención** firmable.

Los puntos 1–3 son el núcleo del propósito nuevo: sin ellos el módulo sigue
siendo un tablero de tareas por muy pulido que esté el frontend.
