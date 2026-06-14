# Banco oficial de tipos de documento — España (FV)

Investigación del segundo commit del framework de documentos. Objetivo: sembrar las
plantillas oficiales (system, `org_id` NULL, `scope='system'`, `country='ES'`) que un
instalador fotovoltaico español necesita a lo largo del ciclo de un proyecto, cada una con
contenido por secciones usando el motor de variables, y tagueada con `country`, `required_by`
y `stage` como metadata para un futuro asistente RAG (no se construye ahora).

## Ciclo de vida y etapas (`stage`)

El registro define `TEMPLATE_STAGES = ('diseno', 'legalizacion', 'entrega', 'posventa')`.

- **diseno** — captación y diseño: propuesta comercial/estudio de ahorro, estudio
  estructural de cubierta, contrato de instalación.
- **legalizacion** — tramitación ante Distribuidora / Industria / CCAA: memoria técnica de
  diseño, solicitud de acceso y conexión, CIE.
- **entrega** — cierre: acta de puesta en marcha, certificado de garantía, certificado
  energético (justificante deducción IRPF).
- **posventa** — operación: contrato de mantenimiento, informe de mantenimiento.

## Tipos de documento del instalador FV en España

| Documento | kind | required_by | stage | Notas de dominio |
|---|---|---|---|---|
| Memoria técnica de diseño (MTD) | memoria_calculo | Distribuidora / Industria | legalizacion | Documento técnico que justifica la instalación generadora bajo REBT/ITC-BT-40 y RD 1699/2011. Recoge datos del campo FV, inversor y, si hay, acumulación. |
| Solicitud de acceso y conexión | solicitud_conexion | Distribuidora | legalizacion | Trámite ante la distribuidora para autoconsumo (RD 244/2019). Punto de suministro identificado por CUPS. |
| CIE / Certificado de Instalación Eléctrica | certificado | Industria / CCAA | legalizacion | Boletín eléctrico emitido por instalador autorizado; se presenta ante Industria de la CCAA. |
| Estudio estructural de cubierta | documento_legal | Cliente / Normativa | diseno | Verificación de que la cubierta soporta la sobrecarga del campo FV (CTE DB-SE). |
| Contrato de instalación | contrato | Cliente | diseno | Contrato de obra/suministro entre instalador y cliente. |
| Contrato de mantenimiento | contrato | Cliente | posventa | Servicio recurrente de mantenimiento preventivo/correctivo. |
| Certificado de garantía | certificado | Cliente | entrega | Garantía de equipos y de la instalación. |
| Certificado energético (justificante deducción IRPF) | certificado | Hacienda | entrega | Justifica la mejora de eficiencia para la deducción de IRPF por obras de rehabilitación energética. |
| Acta de puesta en marcha / entrega | certificado | Cliente | entrega | Acta de entrega y puesta en marcha de la instalación (datos de `installation.*`). |
| Informe de mantenimiento | informe_mantenimiento | Cliente | posventa | Parte de una visita: estado, técnico, incidencia relevante (`installation.* + maintenance.* + incident.*`). |
| Propuesta comercial / estudio de ahorro | propuesta_comercial | Cliente | diseno | Oferta económica con métricas financieras (`finance.*`). |

## Glosario do-not-translate (respetar en el contenido)

CUPS, kWp, kW, kWh, Wp, Voc, Isc, Vmp, Imp, MPPT, ITC-BT-40, REBT, RD 1699/2011, RD 244/2019,
CTE DB-SE, IRPF, AC, DC, string, inverter, PVGIS, STC, NOCT. Se quedan literales o se interpolan
como variables; no se traducen.

## Variables del motor por kind (de `catalog.py` / `DOCUMENT_KIND_REGISTRY`)

- `memoria_calculo`: project, panel, inverter, battery, wire, user, org.
- `solicitud_conexion`: project, panel, inverter, battery, wire, user, org.
- `certificado`: grupos de proyecto + posventa (installation, maintenance, incident).
- `documento_legal`: grupos de proyecto + posventa.
- `contrato`: grupos de proyecto + finance + posventa.
- `propuesta_comercial`: grupos de proyecto + finance.
- `informe_mantenimiento`: grupos de proyecto + posventa.

Filtros disponibles: `number(d)`, `thousands(d)`, `money(d)`, `currency`, `date(fmt?)`,
`ellipsis(n)`, `upper`, `lower`. Aritmética: `+ - * / ( )`, `round`, `sum`. Entidades
opcionales (battery, wire, installation, maintenance, incident, finance) resuelven a vacío
cuando no existen, así que el render nunca rompe.

## Decisiones de arquitectura

- **Mecanismo**: comando CLI `flask docs seed`, grupo nuevo `docs_cli` en `app/cli.py`,
  registrado en `register_cli`. Idempotente: salta si ya existe una plantilla por
  `(kind, name, country)`. No toca el seed de flags ni el de equipos.
- **Datos, no esquema**: las plantillas y versiones se crean con los modelos existentes; no
  hay migración nueva (es data sobre tablas ya creadas en el commit 1).
- **Servicio de dominio**: la siembra vive en `app/services/document_bank.py`
  (`DocumentBankSeeder`), sin Flask, reutilizable desde el CLI y desde los tests. El CLI es
  fino: llama al servicio y reporta.
- **Cada plantilla**: `ReportTemplate(org_id=None, scope='system', country='ES', locale='es',`
  `currency='EUR', is_official=True, status='published')` + una `TemplateVersion(version=1,`
  `published_at=now)` con secciones reales `[{id,type,title,body}]`.
- **Idempotencia**: la unicidad lógica es `(kind, name, country)` sobre las plantillas system;
  el seeder consulta antes de crear y devuelve cuántas creó vs. ya existían.

## Puntos abiertos

- Solo ES en este commit. Otros países (FR/DE/IT/PT, ya con perfil de jurisdicción) quedan
  pendientes: cada uno necesita su propio set legal/normativo.
- El contenido es estructura representativa y usable, no el texto legal íntegro de cada
  documento; un revisor legal debería completar las cláusulas antes de uso real.
